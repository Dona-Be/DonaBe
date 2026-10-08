import pytest

from src.core.config import Settings


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://", "postgresql+psycopg://"])
def test_database_url_always_uses_the_psycopg_driver(scheme: str) -> None:
    settings = Settings(_env_file=None, DATABASE_URL=f"{scheme}donabe:secret@db.render.com/donabe")

    assert settings.DATABASE_URL == "postgresql+psycopg://donabe:secret@db.render.com/donabe"
