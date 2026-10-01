from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from src.models import Book, Library, LibraryBooks
from src.seed import SEED_AVAILABLE_COUNT, SEED_BOOK_UID, SEED_LIBRARY_UID, seed_reference_data


def _session(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()


def test_seed_creates_reference_data(client, engine):
    with _session(engine) as session:
        seed_reference_data(session)

        assert session.scalar(select(Library).where(Library.library_uid == SEED_LIBRARY_UID))
        assert session.scalar(select(Book).where(Book.book_uid == SEED_BOOK_UID))


def test_seed_does_not_duplicate_records(client, engine):
    with _session(engine) as session:
        seed_reference_data(session)
        seed_reference_data(session)

        assert len(list(session.scalars(select(Library)))) == 1
        assert len(list(session.scalars(select(Book)))) == 1


def test_seed_restores_available_count(client, engine):
    with _session(engine) as session:
        seed_reference_data(session)
        available = session.scalars(select(LibraryBooks)).one()
        available.available_count = 0
        session.commit()

        seed_reference_data(session)

        assert session.scalars(select(LibraryBooks)).one().available_count == SEED_AVAILABLE_COUNT
