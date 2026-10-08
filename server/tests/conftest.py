import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session

from tests.fakes import FakeGoogleApp, google_token

SERVER_DIR = Path(__file__).resolve().parents[1]
load_dotenv(SERVER_DIR.parent / ".env")

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
MISSING_DATABASE_URL_MESSAGE = (
    "TEST_DATABASE_URL is not set. Point it to a separate PostGIS database, for example "
    "TEST_DATABASE_URL=postgresql+psycopg://donabe:donabe@localhost:5432/donabe_test in the "
    ".env file (the database is created automatically), and start PostGIS with make up."
)
TEST_DATABASE_SUFFIX = "_test"
WRONG_TEST_DATABASE_MESSAGE = (
    "TEST_DATABASE_URL must point to a database whose name ends with _test, because the tests "
    "drop and empty its tables."
)
# The settings are read when src is imported, so the environment is fixed here and src is
# imported lazily inside the fixtures, after this module ran.
os.environ.update(
    {
        "ENVIRONMENT": "development",
        "DATABASE_URL": TEST_DATABASE_URL or "postgresql+psycopg://missing@localhost/missing",
        "SESSION_SECRET_KEY": "test-session-secret-key-with-32-chars-or-more",
        "JWT_SECRET_KEY": "test-jwt-secret-key-with-32-chars-or-more",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
        "FRONTEND_URL": "http://localhost:5173",
    }
)


def create_database_if_missing(url: str) -> None:
    database_url = make_url(url)
    maintenance_engine = create_engine(
        database_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with maintenance_engine.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database_url.database}
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{database_url.database}"'))
    maintenance_engine.dispose()


@pytest.fixture(scope="session")
def database_url_for_tests() -> str:
    if not TEST_DATABASE_URL:
        raise RuntimeError(MISSING_DATABASE_URL_MESSAGE)
    if not (make_url(TEST_DATABASE_URL).database or "").endswith(TEST_DATABASE_SUFFIX):
        raise RuntimeError(WRONG_TEST_DATABASE_MESSAGE)
    create_database_if_missing(TEST_DATABASE_URL)
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    config = Config(str(SERVER_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    return config


@pytest.fixture(scope="session")
def migrated_database(database_url_for_tests: str, alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")


@pytest.fixture
def clean_database(migrated_database: None) -> Iterator[None]:
    from src.core.database import engine
    from src.models import Base

    yield
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db_session(clean_database: None) -> Iterator[Session]:
    from src.core.database import engine

    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def fake_google() -> FakeGoogleApp:
    return FakeGoogleApp(google_token())


@pytest.fixture
def client(clean_database: None, fake_google: FakeGoogleApp) -> Iterator[TestClient]:
    from src.api.dependencies import get_google_client
    from src.auth.google import GoogleClient
    from src.main import app

    app.dependency_overrides[get_google_client] = lambda: GoogleClient(fake_google)
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
