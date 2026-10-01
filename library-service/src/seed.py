import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Book, Library, LibraryBooks
from src.schemas import BookCondition

SEED_LIBRARY_UID = uuid.UUID("83575e12-7ce0-48ee-9931-51919ff3c9ee")
SEED_LIBRARY_NAME = "Библиотека имени 7 Непьющих"
SEED_LIBRARY_CITY = "Москва"
SEED_LIBRARY_ADDRESS = "2-я Бауманская ул., д.5, стр.1"

SEED_BOOK_UID = uuid.UUID("f7cdc58f-2caf-4b15-9727-f89dcc629b27")
SEED_BOOK_NAME = "Краткий курс C++ в 7 томах"
SEED_BOOK_AUTHOR = "Бьерн Страуструп"
SEED_BOOK_GENRE = "Научная фантастика"
SEED_BOOK_CONDITION = BookCondition.EXCELLENT
SEED_AVAILABLE_COUNT = 1


def seed_reference_data(session: Session) -> None:
    """Заполняет каталог данными варианта.

    Библиотека и книга создаются один раз: на их идентификаторы ссылаются брони.
    Счётчик экземпляров, наоборот, восстанавливается при каждом старте — иначе
    прогон, прерванный между выдачей и возвратом, оставит каталог пустым.
    """
    library = session.scalar(select(Library).where(Library.library_uid == SEED_LIBRARY_UID))
    if library is None:
        library = Library(
            library_uid=SEED_LIBRARY_UID,
            name=SEED_LIBRARY_NAME,
            city=SEED_LIBRARY_CITY,
            address=SEED_LIBRARY_ADDRESS,
        )
        session.add(library)

    book = session.scalar(select(Book).where(Book.book_uid == SEED_BOOK_UID))
    if book is None:
        book = Book(
            book_uid=SEED_BOOK_UID,
            name=SEED_BOOK_NAME,
            author=SEED_BOOK_AUTHOR,
            genre=SEED_BOOK_GENRE,
            condition=SEED_BOOK_CONDITION,
        )
        session.add(book)

    session.flush()

    available = session.get(LibraryBooks, (book.id, library.id))
    if available is None:
        session.add(
            LibraryBooks(
                book_id=book.id,
                library_id=library.id,
                available_count=SEED_AVAILABLE_COUNT,
            )
        )
    else:
        available.available_count = SEED_AVAILABLE_COUNT

    session.commit()
