import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.config import normalize_database_url
from src.database import Base, get_db
from src.main import app

DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://program:test@localhost:5432/ratings_test"
TRUNCATE_RATING = "TRUNCATE TABLE rating RESTART IDENTITY CASCADE"


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
        connection.execute(text(TRUNCATE_RATING))

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
