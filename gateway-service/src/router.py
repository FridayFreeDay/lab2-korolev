import uuid

from fastapi import APIRouter, Depends, Header, Query, Response, status

from src import clients, service
from src.schemas import (
    BookReservationResponse,
    ErrorResponse,
    LibraryBookResponse,
    LibraryResponse,
    PageResponse,
    ReturnBookRequest,
    TakeBookRequest,
    TakeBookResponse,
    UserRatingResponse,
    ValidationErrorResponse,
)

API_PREFIX = "/api/v1"
USER_NAME_HEADER = "X-User-Name"

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}
BAD_REQUEST = {status.HTTP_400_BAD_REQUEST: {"model": ValidationErrorResponse}}

router = APIRouter(prefix=API_PREFIX, tags=["Gateway API"])


def user_name(raw: str = Header(alias=USER_NAME_HEADER)) -> str:
    """Возвращает имя в UTF-8: заголовки приходят декодированными как latin-1."""
    try:
        return raw.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return raw


@router.get("/libraries", response_model=PageResponse[LibraryResponse])
async def list_libraries(
    city: str,
    page: int = Query(DEFAULT_PAGE, ge=0),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> PageResponse[LibraryResponse]:
    return PageResponse[LibraryResponse].model_validate(
        await clients.list_libraries(city, page, size)
    )


@router.get(
    "/libraries/{library_uid}/books",
    response_model=PageResponse[LibraryBookResponse],
    responses=NOT_FOUND,
)
async def list_library_books(
    library_uid: uuid.UUID,
    show_all: bool = Query(False, alias="showAll"),
    page: int = Query(DEFAULT_PAGE, ge=0),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> PageResponse[LibraryBookResponse]:
    return PageResponse[LibraryBookResponse].model_validate(
        await clients.list_library_books(library_uid, show_all, page, size)
    )


@router.get("/reservations", response_model=list[BookReservationResponse])
async def list_reservations(
    username: str = Depends(user_name),
) -> list[BookReservationResponse]:
    return await service.list_user_reservations(username)


@router.post("/reservations", response_model=TakeBookResponse, responses=BAD_REQUEST)
async def take_book(
    request: TakeBookRequest, username: str = Depends(user_name)
) -> TakeBookResponse:
    return await service.rent_book(username, request)


@router.post(
    "/reservations/{reservation_uid}/return",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
async def return_book(
    reservation_uid: uuid.UUID,
    request: ReturnBookRequest,
    username: str = Depends(user_name),
) -> Response:
    await service.return_book(username, reservation_uid, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/rating", response_model=UserRatingResponse)
async def get_rating(
    username: str = Depends(user_name),
) -> UserRatingResponse:
    return await service.get_user_rating(username)
