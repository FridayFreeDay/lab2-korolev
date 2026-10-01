import uuid
from typing import Any

import httpx

from src.config import (
    CONNECT_TIMEOUT_SECONDS,
    MAX_CONNECTIONS,
    MAX_KEEPALIVE_CONNECTIONS,
    POOL_TIMEOUT_SECONDS,
    READ_TIMEOUT_SECONDS,
    settings,
)
from src.errors import (
    BookNotAvailableError,
    ServiceUnavailableError,
    UpstreamBadRequestError,
    UpstreamNotFoundError,
)

LIBRARY_SERVICE = "Library Service"
RESERVATION_SERVICE = "Reservation Service"
RATING_SERVICE = "Rating Service"
USER_NAME_HEADER = "X-User-Name"
UID_SEPARATOR = ","

_client: httpx.AsyncClient | None = None


def open_client() -> None:
    global _client
    _client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=CONNECT_TIMEOUT_SECONDS,
            read=READ_TIMEOUT_SECONDS,
            write=READ_TIMEOUT_SECONDS,
            pool=POOL_TIMEOUT_SECONDS,
        ),
        limits=httpx.Limits(
            max_connections=MAX_CONNECTIONS,
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
        ),
    )


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def get_client() -> httpx.AsyncClient:
    if _client is None:
        raise ServiceUnavailableError("Gateway")
    return _client


async def _request(
    service: str,
    method: str,
    base_url: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    username: str | None = None,
) -> Any:
    """Выполняет вызов сервиса, переводя его ответ в доменные ошибки шлюза.

    Любая сетевая проблема и любая 5xx превращаются в 503: наружу не должны
    протекать подробности того, какой именно сервис и как именно сломался.
    """
    headers = {USER_NAME_HEADER: username} if username is not None else None
    try:
        response = await get_client().request(
            method, f"{base_url}{path}", params=params, json=json, headers=headers
        )
    except httpx.HTTPError as error:
        raise ServiceUnavailableError(service) from error

    if response.status_code == httpx.codes.NOT_FOUND:
        raise UpstreamNotFoundError(_message(response))
    if response.status_code == httpx.codes.CONFLICT:
        raise BookNotAvailableError
    if response.status_code in (httpx.codes.BAD_REQUEST, httpx.codes.UNPROCESSABLE_ENTITY):
        raise UpstreamBadRequestError(_message(response))
    if response.status_code >= httpx.codes.INTERNAL_SERVER_ERROR:
        raise ServiceUnavailableError(service)

    return response.json()


def _message(response: httpx.Response) -> str:
    try:
        return response.json().get("message", response.text)
    except ValueError:
        return response.text


async def list_libraries(city: str, page: int, size: int) -> dict[str, Any]:
    return await _request(
        LIBRARY_SERVICE,
        "GET",
        settings.library_service_url,
        "/api/v1/libraries",
        params={"city": city, "page": page, "size": size},
    )


async def list_library_books(
    library_uid: uuid.UUID, show_all: bool, page: int, size: int
) -> dict[str, Any]:
    return await _request(
        LIBRARY_SERVICE,
        "GET",
        settings.library_service_url,
        f"/api/v1/libraries/{library_uid}/books",
        params={"showAll": show_all, "page": page, "size": size},
    )


async def get_library(library_uid: uuid.UUID) -> dict[str, Any]:
    return await _request(
        LIBRARY_SERVICE,
        "GET",
        settings.library_service_url,
        f"/api/v1/libraries/{library_uid}",
    )


async def get_book(book_uid: uuid.UUID) -> dict[str, Any]:
    return await _request(
        LIBRARY_SERVICE, "GET", settings.library_service_url, f"/api/v1/books/{book_uid}"
    )


async def lookup_libraries(library_uids: list[uuid.UUID]) -> list[dict[str, Any]]:
    if not library_uids:
        return []
    return await _request(
        LIBRARY_SERVICE,
        "GET",
        settings.library_service_url,
        "/api/v1/lookup/libraries",
        params={"uids": UID_SEPARATOR.join(str(uid) for uid in library_uids)},
    )


async def lookup_books(book_uids: list[uuid.UUID]) -> list[dict[str, Any]]:
    if not book_uids:
        return []
    return await _request(
        LIBRARY_SERVICE,
        "GET",
        settings.library_service_url,
        "/api/v1/lookup/books",
        params={"uids": UID_SEPARATOR.join(str(uid) for uid in book_uids)},
    )


async def take_book(library_uid: uuid.UUID, book_uid: uuid.UUID) -> dict[str, Any]:
    return await _request(
        LIBRARY_SERVICE,
        "POST",
        settings.library_service_url,
        f"/api/v1/libraries/{library_uid}/books/{book_uid}/take",
    )


async def return_book(library_uid: uuid.UUID, book_uid: uuid.UUID) -> dict[str, Any]:
    return await _request(
        LIBRARY_SERVICE,
        "POST",
        settings.library_service_url,
        f"/api/v1/libraries/{library_uid}/books/{book_uid}/return",
    )


async def list_reservations(
    username: str, status: str | None = None
) -> list[dict[str, Any]]:
    return await _request(
        RESERVATION_SERVICE,
        "GET",
        settings.reservation_service_url,
        "/api/v1/reservations",
        params={"status": status} if status else None,
        username=username,
    )


async def create_reservation(username: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _request(
        RESERVATION_SERVICE,
        "POST",
        settings.reservation_service_url,
        "/api/v1/reservations",
        json=payload,
        username=username,
    )


async def close_reservation(
    username: str, reservation_uid: uuid.UUID, payload: dict[str, Any]
) -> dict[str, Any]:
    return await _request(
        RESERVATION_SERVICE,
        "POST",
        settings.reservation_service_url,
        f"/api/v1/reservations/{reservation_uid}/return",
        json=payload,
        username=username,
    )


async def get_rating(username: str) -> dict[str, Any]:
    return await _request(
        RATING_SERVICE,
        "GET",
        settings.rating_service_url,
        "/api/v1/rating",
        username=username,
    )


async def update_rating(username: str, delta: int) -> dict[str, Any]:
    return await _request(
        RATING_SERVICE,
        "PATCH",
        settings.rating_service_url,
        "/api/v1/rating",
        json={"delta": delta},
        username=username,
    )
