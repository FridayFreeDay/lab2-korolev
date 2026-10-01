import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src import repository
from src.database import get_db
from src.models import Book
from src.schemas import (
    AvailableCountResponse,
    BookResponse,
    ErrorResponse,
    LibraryBookResponse,
    LibraryResponse,
    PageResponse,
)

LIBRARIES_PREFIX = "/api/v1/libraries"
BOOKS_PREFIX = "/api/v1/books"
LOOKUP_PREFIX = "/api/v1/lookup"

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
UID_SEPARATOR = ","

TAKE_DELTA = -1
RETURN_DELTA = 1

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}

libraries_router = APIRouter(prefix=LIBRARIES_PREFIX, tags=["Library"])
books_router = APIRouter(prefix=BOOKS_PREFIX, tags=["Library"])
lookup_router = APIRouter(prefix=LOOKUP_PREFIX, tags=["Library"])


def _parse_uids(uids: str) -> list[uuid.UUID]:
    return [uuid.UUID(value) for value in uids.split(UID_SEPARATOR) if value]


def _to_library_book(book: Book, available_count: int) -> LibraryBookResponse:
    return LibraryBookResponse(
        book_uid=book.book_uid,
        name=book.name,
        author=book.author,
        genre=book.genre,
        condition=book.condition,
        available_count=available_count,
    )


@libraries_router.get("", response_model=PageResponse[LibraryResponse])
def list_libraries(
    city: str,
    page: int = Query(DEFAULT_PAGE, ge=0),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    session: Session = Depends(get_db),
) -> PageResponse[LibraryResponse]:
    libraries, total = repository.list_libraries(session, city, page, size)
    return PageResponse[LibraryResponse](
        page=page,
        page_size=size,
        total_elements=total,
        items=[LibraryResponse.model_validate(library) for library in libraries],
    )


@libraries_router.get("/{library_uid}", response_model=LibraryResponse, responses=NOT_FOUND)
def get_library(
    library_uid: uuid.UUID, session: Session = Depends(get_db)
) -> LibraryResponse:
    return LibraryResponse.model_validate(repository.get_library(session, library_uid))


@libraries_router.get(
    "/{library_uid}/books",
    response_model=PageResponse[LibraryBookResponse],
    responses=NOT_FOUND,
)
def list_library_books(
    library_uid: uuid.UUID,
    show_all: bool = Query(False, alias="showAll"),
    page: int = Query(DEFAULT_PAGE, ge=0),
    size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    session: Session = Depends(get_db),
) -> PageResponse[LibraryBookResponse]:
    rows, total = repository.list_library_books(session, library_uid, show_all, page, size)
    return PageResponse[LibraryBookResponse](
        page=page,
        page_size=size,
        total_elements=total,
        items=[_to_library_book(book, available_count) for book, available_count in rows],
    )


@libraries_router.post(
    "/{library_uid}/books/{book_uid}/take",
    response_model=AvailableCountResponse,
    responses=NOT_FOUND,
)
def take_book(
    library_uid: uuid.UUID, book_uid: uuid.UUID, session: Session = Depends(get_db)
) -> AvailableCountResponse:
    available_count = repository.change_available_count(
        session, library_uid, book_uid, TAKE_DELTA
    )
    return AvailableCountResponse(available_count=available_count)


@libraries_router.post(
    "/{library_uid}/books/{book_uid}/return",
    response_model=AvailableCountResponse,
    responses=NOT_FOUND,
)
def return_book(
    library_uid: uuid.UUID, book_uid: uuid.UUID, session: Session = Depends(get_db)
) -> AvailableCountResponse:
    available_count = repository.change_available_count(
        session, library_uid, book_uid, RETURN_DELTA
    )
    return AvailableCountResponse(available_count=available_count)


@books_router.get("/{book_uid}", response_model=BookResponse, responses=NOT_FOUND)
def get_book(book_uid: uuid.UUID, session: Session = Depends(get_db)) -> BookResponse:
    return BookResponse.model_validate(repository.get_book(session, book_uid))


@lookup_router.get("/libraries", response_model=list[LibraryResponse])
def lookup_libraries(
    uids: str, session: Session = Depends(get_db)
) -> list[LibraryResponse]:
    libraries = repository.get_libraries_by_uids(session, _parse_uids(uids))
    return [LibraryResponse.model_validate(library) for library in libraries]


@lookup_router.get("/books", response_model=list[BookResponse])
def lookup_books(uids: str, session: Session = Depends(get_db)) -> list[BookResponse]:
    books = repository.get_books_by_uids(session, _parse_uids(uids))
    return [BookResponse.model_validate(book) for book in books]
