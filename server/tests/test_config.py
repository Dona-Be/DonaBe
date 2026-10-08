import pytest
from pydantic import ValidationError

from src.core.config import Settings


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://", "postgresql+psycopg://"])
def test_database_url_always_uses_the_psycopg_driver(scheme: str) -> None:
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        DATABASE_URL=f"{scheme}donabe:secret@db.render.com/donabe",
    )

    assert settings.DATABASE_URL == "postgresql+psycopg://donabe:secret@db.render.com/donabe"


@pytest.mark.parametrize(
    "database_url",
    [
        pytest.param("postgresql://donabe:secret@localhost:5432/donabe", id="localhost"),
        pytest.param("postgresql://donabe:secret@LOCALHOST/donabe", id="upper case"),
        pytest.param("postgresql://donabe:secret@localhost./donabe", id="trailing dot"),
        pytest.param("postgresql://donabe:secret@127.0.0.1:5432/donabe", id="loopback"),
        pytest.param("postgresql://donabe:secret@127.0.0.2/donabe", id="other loopback"),
        pytest.param("postgresql://donabe:secret@0.0.0.0/donabe", id="any address"),
        pytest.param("postgresql://donabe:secret@[::1]/donabe", id="ipv6 loopback"),
        pytest.param("postgresql:///donabe", id="no host means the local socket"),
        pytest.param(
            "postgresql://donabe:secret@/donabe?host=/var/run/postgresql", id="socket directory"
        ),
        pytest.param(
            "postgresql://donabe:secret@db.render.com/donabe?host=localhost",
            id="host in the query string",
        ),
        pytest.param(
            "postgresql://donabe:secret@localhost:${POSTGRES_PORT}/donabe", id="unexpanded port"
        ),
        pytest.param("postgresql://donabe:secret@${DATABASE_HOST}/donabe", id="unexpanded host"),
    ],
)
def test_production_refuses_a_local_or_unexpanded_database_url(database_url: str) -> None:
    with pytest.raises(ValidationError, match="Internal Database URL"):
        Settings(_env_file=None, ENVIRONMENT="production", DATABASE_URL=database_url)


@pytest.mark.parametrize("host", ["dpg-abc123-a", "db.render.com"])
def test_production_accepts_a_remote_database_url(host: str) -> None:
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        DATABASE_URL=f"postgresql://donabe:secret@{host}/donabe",
    )

    assert settings.DATABASE_URL == f"postgresql+psycopg://donabe:secret@{host}/donabe"


def test_development_accepts_a_local_database_url() -> None:
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        DATABASE_URL="postgresql://donabe:secret@localhost:5432/donabe",
    )

    assert settings.DATABASE_URL == "postgresql+psycopg://donabe:secret@localhost:5432/donabe"
