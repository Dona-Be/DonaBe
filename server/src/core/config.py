from ipaddress import ip_address
from typing import Literal, Self
from urllib.parse import parse_qs, urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

POSTGRES_SCHEMES_WITHOUT_DRIVER = ("postgres://", "postgresql://")
PSYCOPG_SCHEME = "postgresql+psycopg://"
MIN_SECRET_LENGTH = 32
LOCAL_HOST_NAMES = frozenset({"", "localhost"})
UNIX_SOCKET_PREFIX = "/"
UNEXPANDED_VARIABLE = "${"
DEVELOPMENT_DATABASE_URL_IN_PRODUCTION = (
    "DATABASE_URL points to this machine or still contains ${...}. "
    "In production, use the Internal Database URL of the Render database."
)


def use_psycopg_driver(database_url: str) -> str:
    for scheme in POSTGRES_SCHEMES_WITHOUT_DRIVER:
        if database_url.startswith(scheme):
            return PSYCOPG_SCHEME + database_url.removeprefix(scheme)
    return database_url


def is_this_machine(host: str) -> bool:
    normalized = host.rstrip(".").lower()
    if normalized in LOCAL_HOST_NAMES or normalized.startswith(UNIX_SOCKET_PREFIX):
        return True
    try:
        address = ip_address(normalized)
    except ValueError:
        return False
    return address.is_loopback or address.is_unspecified


def database_hosts(database_url: str) -> list[str]:
    parts = urlsplit(database_url)
    return [parts.hostname or "", *parse_qs(parts.query).get("host", [])]


def points_to_this_machine(database_url: str) -> bool:
    return any(is_this_machine(host) for host in database_hosts(database_url))


def has_unexpanded_variable(database_url: str) -> bool:
    return UNEXPANDED_VARIABLE in database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        case_sensitive=True,
        extra="ignore",
        hide_input_in_errors=True,
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

    @model_validator(mode="after")
    def reject_development_database_url_in_production(self) -> Self:
        database_url = self.DATABASE_URL
        if self.is_production and (
            points_to_this_machine(database_url) or has_unexpanded_variable(database_url)
        ):
            raise ValueError(DEVELOPMENT_DATABASE_URL_IN_PRODUCTION)
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def frontend_page(self, path: str = "") -> str:
        return self.FRONTEND_URL.rstrip("/") + path


settings = Settings()
