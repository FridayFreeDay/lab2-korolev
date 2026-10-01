import os
import uuid

os.environ.setdefault("SEED_ON_STARTUP", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from src.config import normalize_database_url  # noqa: E402
from src.database import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402

DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://program:test@localhost:5432/libraries_test"
TRUNCATE_TABLES = "TRUNCATE TABLE library_books, books, library RESTART IDENTITY CASCADE"


@pytest.fixture(scope="session")
def engine():
    url = normalize_database_url(
        os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    )
    engine = create_engine(url, pool_pre_ping=True, future=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(engine):
    with engine.begin() as connection:
        connection.execute(text(TRUNCATE_TABLES))

    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def catalog(engine):
    """Библиотека с двумя книгами: одна доступна, вторая разобрана."""
    from src.models import Book, Library, LibraryBooks

    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with TestingSession() as session:
        library = Library(
            library_uid=uuid.UUID("83575e12-7ce0-48ee-9931-51919ff3c9ee"),
            name="Библиотека имени 7 Непьющих",
            city="Москва",
            address="2-я Бауманская ул., д.5, стр.1",
        )
        other_library = Library(
            library_uid=uuid.uuid4(), name="Другая", city="Казань", address="Улица"
        )
        available = Book(
            book_uid=uuid.UUID("f7cdc58f-2caf-4b15-9727-f89dcc629b27"),
            name="Краткий курс C++ в 7 томах",
            author="Бьерн Страуструп",
            genre="Научная фантастика",
            condition="EXCELLENT",
        )
        taken = Book(book_uid=uuid.uuid4(), name="Разобранная", condition="GOOD")
        session.add_all([library, other_library, available, taken])
        session.flush()
        session.add_all(
            [
                LibraryBooks(book_id=available.id, library_id=library.id, available_count=1),
                LibraryBooks(book_id=taken.id, library_id=library.id, available_count=0),
            ]
        )
        session.commit()
        return {
            "library_uid": library.library_uid,
            "other_library_uid": other_library.library_uid,
            "available_book_uid": available.book_uid,
            "taken_book_uid": taken.book_uid,
        }
