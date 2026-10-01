import uuid
from collections.abc import Sequence

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from src.errors import BookNotAvailableError, BookNotFoundError, LibraryNotFoundError
from src.models import Book, Library, LibraryBooks

FIRST_PAGE = 1
MIN_AVAILABLE_COUNT = 0


def _offset(page: int, size: int) -> int:
    return max(page - FIRST_PAGE, 0) * size


def _count(session: Session, statement: Select) -> int:
    return session.scalar(select(func.count()).select_from(statement.subquery())) or 0


def get_library(session: Session, library_uid: uuid.UUID) -> Library:
    library = session.scalar(select(Library).where(Library.library_uid == library_uid))
    if library is None:
        raise LibraryNotFoundError(library_uid)
    return library


def get_book(session: Session, book_uid: uuid.UUID) -> Book:
    book = session.scalar(select(Book).where(Book.book_uid == book_uid))
    if book is None:
        raise BookNotFoundError(book_uid)
    return book


def get_libraries_by_uids(
    session: Session, library_uids: Sequence[uuid.UUID]
) -> list[Library]:
    if not library_uids:
        return []
    statement = select(Library).where(Library.library_uid.in_(library_uids))
    return list(session.scalars(statement))


def get_books_by_uids(session: Session, book_uids: Sequence[uuid.UUID]) -> list[Book]:
    if not book_uids:
        return []
    statement = select(Book).where(Book.book_uid.in_(book_uids))
    return list(session.scalars(statement))


def list_libraries(
    session: Session, city: str, page: int, size: int
) -> tuple[list[Library], int]:
    statement = select(Library).where(Library.city == city)
    total = _count(session, statement)
    libraries = session.scalars(
        statement.order_by(Library.id).offset(_offset(page, size)).limit(size)
    )
    return list(libraries), total


def list_library_books(
    session: Session, library_uid: uuid.UUID, show_all: bool, page: int, size: int
) -> tuple[list[tuple[Book, int]], int]:
    library = get_library(session, library_uid)
    statement = (
        select(Book, LibraryBooks.available_count)
        .join(LibraryBooks, LibraryBooks.book_id == Book.id)
        .where(LibraryBooks.library_id == library.id)
    )
    if not show_all:
        statement = statement.where(LibraryBooks.available_count > MIN_AVAILABLE_COUNT)

    total = _count(session, statement)
    rows = session.execute(
        statement.order_by(Book.id).offset(_offset(page, size)).limit(size)
    ).all()
    return [(row[0], row[1]) for row in rows], total


def change_available_count(
    session: Session, library_uid: uuid.UUID, book_uid: uuid.UUID, delta: int
) -> int:
    """Меняет счётчик доступных экземпляров одним UPDATE.

    Условие на неотрицательный остаток стоит внутри запроса, поэтому
    параллельные выдачи одной последней книги не могут увести счётчик в минус.
    """
    library = get_library(session, library_uid)
    book = get_book(session, book_uid)

    statement = (
        update(LibraryBooks)
        .where(
            LibraryBooks.library_id == library.id,
            LibraryBooks.book_id == book.id,
            LibraryBooks.available_count + delta >= MIN_AVAILABLE_COUNT,
        )
        .values(available_count=LibraryBooks.available_count + delta)
        .returning(LibraryBooks.available_count)
    )
    available_count = session.scalar(statement)
    if available_count is None:
        session.rollback()
        raise BookNotAvailableError(book_uid, library_uid)

    session.commit()
    return available_count
