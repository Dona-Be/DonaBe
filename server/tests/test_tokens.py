from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest

from src.auth.tokens import (
    JWT_ALGORITHM,
    MAX_USER_ID,
    TokenSession,
    issue_access_token,
    issue_pending_signup_token,
    read_access_token,
    read_pending_signup_token,
)
from src.core.config import settings
from src.domain.user_profile import UserProfile
from tests.fakes import USER_EMAIL, USER_NAME, USER_PICTURE

PROFILE = UserProfile(email=USER_EMAIL, name=USER_NAME, picture_url=USER_PICTURE)
USER_ID = 42
SESSION_VERSION = 3


def access_claims(**overrides: Any) -> dict[str, Any]:
    claims = jwt.decode(
        issue_access_token(USER_ID, SESSION_VERSION),
        settings.JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )
    return {**claims, **overrides}


def sign(claims: dict[str, Any], key: str = settings.JWT_SECRET_KEY) -> str:
    return jwt.encode(claims, key, JWT_ALGORITHM)


def test_access_token_round_trip() -> None:
    assert read_access_token(issue_access_token(USER_ID, SESSION_VERSION)) == TokenSession(
        user_id=USER_ID, session_version=SESSION_VERSION
    )


def test_pending_signup_token_round_trip() -> None:
    assert read_pending_signup_token(issue_pending_signup_token(PROFILE)) == PROFILE


def test_token_of_another_purpose_is_rejected() -> None:
    assert read_access_token(issue_pending_signup_token(PROFILE)) is None
    assert read_pending_signup_token(issue_access_token(USER_ID, SESSION_VERSION)) is None


def test_tampered_token_is_rejected() -> None:
    token = issue_access_token(USER_ID, SESSION_VERSION)

    assert read_access_token(token[:-2] + "xx") is None
    assert (
        read_access_token(sign(access_claims(), "another-secret-key-with-32-chars-or-more")) is None
    )


def test_expired_access_token_is_rejected() -> None:
    expired = access_claims(exp=datetime.now(UTC) - timedelta(minutes=1))

    assert read_access_token(sign(expired)) is None


@pytest.mark.parametrize("subject", ["abc", "0", str(MAX_USER_ID + 1)])
def test_access_token_with_subject_outside_the_database_range_is_rejected(subject: str) -> None:
    assert read_access_token(sign(access_claims(sub=subject))) is None


@pytest.mark.parametrize("session_version", [True, "3", 3.5])
def test_access_token_with_a_non_integer_session_version_is_rejected(
    session_version: object,
) -> None:
    assert read_access_token(sign(access_claims(ver=session_version))) is None


def test_access_token_with_the_largest_user_id_is_accepted() -> None:
    session = read_access_token(sign(access_claims(sub=str(MAX_USER_ID))))

    assert session == TokenSession(user_id=MAX_USER_ID, session_version=SESSION_VERSION)
