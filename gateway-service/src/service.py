import asyncio
import uuid
from typing import Any

from src import clients
from src.errors import RentalLimitReachedError
from src.schemas import (
    BookInfo,
    BookReservationResponse,
    LibraryResponse,
    ReservationStatus,
    ReturnBookRequest,
    TakeBookRequest,
    TakeBookResponse,
    UserRatingResponse,
)

CONDITION_RANK = {"BAD": 1, "GOOD": 2, "EXCELLENT": 3}
EXPIRED_PENALTY = -10
CONDITION_PENALTY = -10
IN_TIME_BONUS = 1


def _by_uid(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {item[key]: item for item in items}


async def get_user_rating(username: str) -> UserRatingResponse:
    return UserRatingResponse.model_validate(await clients.get_rating(username))


async def list_user_reservations(username: str) -> list[BookReservationResponse]:
    """Собирает брони пользователя, дополняя их данными каталога.

    Книги и библиотеки запрашиваются пачкой, а не по одной на бронь,
    иначе на каждую запись приходилось бы по два лишних вызова.
    """
    reservations = await clients.list_reservations(username)
    if not reservations:
        return []

    book_uids = list({item["bookUid"] for item in reservations})
    library_uids = list({item["libraryUid"] for item in reservations})
    books, libraries = await asyncio.gather(
        clients.lookup_books(book_uids), clients.lookup_libraries(library_uids)
    )
    books_by_uid = _by_uid(books, "bookUid")
    libraries_by_uid = _by_uid(libraries, "libraryUid")

    return [
        BookReservationResponse(
            reservation_uid=item["reservationUid"],
            status=item["status"],
            start_date=item["startDate"],
            till_date=item["tillDate"],
            book=BookInfo.model_validate(books_by_uid[item["bookUid"]]),
            library=LibraryResponse.model_validate(libraries_by_uid[item["libraryUid"]]),
        )
        for item in reservations
        if item["bookUid"] in books_by_uid and item["libraryUid"] in libraries_by_uid
    ]


async def rent_book(username: str, request: TakeBookRequest) -> TakeBookResponse:
    """Выдаёт книгу, если звёзд рейтинга хватает на ещё одну аренду.

    Все проверки выполняются до изменений: счётчик экземпляров уменьшается
    только после того, как лимит подтверждён.
    """
    library, book = await asyncio.gather(
        clients.get_library(request.library_uid), clients.get_book(request.book_uid)
    )
    rating, rented = await asyncio.gather(
        clients.get_rating(username),
        clients.list_reservations(username, ReservationStatus.RENTED),
    )

    if len(rented) >= rating["stars"]:
        raise RentalLimitReachedError

    await clients.take_book(request.library_uid, request.book_uid)
    reservation = await clients.create_reservation(
        username,
        {
            "bookUid": str(request.book_uid),
            "libraryUid": str(request.library_uid),
            "tillDate": request.till_date.isoformat(),
        },
    )

    return TakeBookResponse(
        reservation_uid=reservation["reservationUid"],
        status=reservation["status"],
        start_date=reservation["startDate"],
        till_date=reservation["tillDate"],
        book=BookInfo.model_validate(book),
        library=LibraryResponse.model_validate(library),
        rating=UserRatingResponse.model_validate(rating),
    )


async def return_book(
    username: str, reservation_uid: uuid.UUID, request: ReturnBookRequest
) -> None:
    reservation = await clients.close_reservation(
        username, reservation_uid, {"date": request.date.isoformat()}
    )
    library_uid = uuid.UUID(reservation["libraryUid"])
    book_uid = uuid.UUID(reservation["bookUid"])

    _, book = await asyncio.gather(
        clients.return_book(library_uid, book_uid), clients.get_book(book_uid)
    )

    await clients.update_rating(
        username, _rating_delta(reservation["status"], request.condition, book["condition"])
    )


def _rating_delta(status: str, returned_condition: str, original_condition: str) -> int:
    """Штрафует за просрочку и за порчу по отдельности, иначе поощряет."""
    delta = 0
    if status == ReservationStatus.EXPIRED:
        delta += EXPIRED_PENALTY
    if CONDITION_RANK[returned_condition] < CONDITION_RANK[original_condition]:
        delta += CONDITION_PENALTY
    return delta if delta else IN_TIME_BONUS
