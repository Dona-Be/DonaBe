from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

POSTGRES_SCHEMES_WITHOUT_DRIVER = ("postgres://", "postgresql://")
PSYCOPG_SCHEME = "postgresql+psycopg://"
MIN_SECRET_LENGTH = 32


def use_psycopg_driver(database_url: str) -> str:
    for scheme in POSTGRES_SCHEMES_WITHOUT_DRIVER:
        if database_url.startswith(scheme):
            return PSYCOPG_SCHEME + database_url.removeprefix(scheme)
    return database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "production"]

    DATABASE_URL: str

    SESSION_SECRET_KEY: str = Field(min_length=MIN_SECRET_LENGTH)
    JWT_SECRET_KEY: str = Field(min_length=MIN_SECRET_LENGTH)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, database_url: str) -> str:
        return use_psycopg_driver(database_url)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def frontend_page(self, path: str = "") -> str:
        return self.FRONTEND_URL.rstrip("/") + path


settings = Settings()
