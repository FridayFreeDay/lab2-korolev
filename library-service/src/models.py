import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

MAX_NAME_LENGTH = 80
MAX_TITLE_LENGTH = 255
MAX_CITY_LENGTH = 255
MAX_ADDRESS_LENGTH = 255
MAX_CONDITION_LENGTH = 20
BOOK_CONDITIONS = ("EXCELLENT", "GOOD", "BAD")
DEFAULT_CONDITION = "EXCELLENT"


class Library(Base):
    __tablename__ = "library"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    library_uid: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(MAX_NAME_LENGTH), nullable=False)
    city: Mapped[str] = mapped_column(String(MAX_CITY_LENGTH), nullable=False)
    address: Mapped[str] = mapped_column(String(MAX_ADDRESS_LENGTH), nullable=False)


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint(
            "condition IN ('EXCELLENT', 'GOOD', 'BAD')", name="books_condition_values"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_uid: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH), nullable=False)
    author: Mapped[str | None] = mapped_column(String(MAX_TITLE_LENGTH), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(MAX_TITLE_LENGTH), nullable=True)
    condition: Mapped[str] = mapped_column(
        String(MAX_CONDITION_LENGTH), nullable=False, default=DEFAULT_CONDITION
    )


class LibraryBooks(Base):
    """Наличие книги в библиотеке.

    В схеме варианта у таблицы нет первичного ключа; составной PK добавлен,
    потому что ORM-класс без него не мапится, а пара (книга, библиотека)
    и так уникальна по смыслу.
    """

    __tablename__ = "library_books"

    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), primary_key=True)
    library_id: Mapped[int] = mapped_column(ForeignKey("library.id"), primary_key=True)
    available_count: Mapped[int] = mapped_column(Integer, nullable=False)
