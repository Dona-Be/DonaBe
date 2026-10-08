from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.core.config import settings
from src.domain.user_profile import UserProfile

JWT_ALGORITHM = "HS256"
ACCESS_PURPOSE = "access"
PENDING_SIGNUP_PURPOSE = "pending_signup"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
PENDING_SIGNUP_LIFETIME = timedelta(minutes=30)
ACCESS_CLAIMS = ["exp", "sub", "ver"]
PENDING_SIGNUP_CLAIMS = ["exp", "sub", "name"]
MAX_USER_ID = 2_147_483_647


@dataclass(frozen=True)
class TokenSession:
    user_id: int
    session_version: int


def issue_token(purpose: str, claims: dict[str, Any], lifetime: timedelta) -> str:
    payload = {**claims, "purpose": purpose, "exp": datetime.now(UTC) + lifetime}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def read_token(purpose: str, token: str, required_claims: list[str]) -> dict[str, Any] | None:
    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": required_claims},
        )
    except jwt.PyJWTError:
        return None
    return claims if claims.get("purpose") == purpose else None


def issue_access_token(user_id: int, session_version: int) -> str:
    claims = {"sub": str(user_id), "ver": session_version}
    return issue_token(ACCESS_PURPOSE, claims, ACCESS_TOKEN_LIFETIME)


def read_access_token(token: str) -> TokenSession | None:
    claims = read_token(ACCESS_PURPOSE, token, ACCESS_CLAIMS)
    if claims is None:
        return None
    try:
        user_id = int(claims["sub"])
    except ValueError:
        return None
    session_version = claims["ver"]
    if not 1 <= user_id <= MAX_USER_ID or not isinstance(session_version, int):
        return None
    return TokenSession(user_id=user_id, session_version=session_version)


def issue_pending_signup_token(profile: UserProfile) -> str:
    claims = {"sub": profile.email, "name": profile.name, "picture_url": profile.picture_url}
    return issue_token(PENDING_SIGNUP_PURPOSE, claims, PENDING_SIGNUP_LIFETIME)


def read_pending_signup_token(token: str) -> UserProfile | None:
    claims = read_token(PENDING_SIGNUP_PURPOSE, token, PENDING_SIGNUP_CLAIMS)
    if claims is None:
        return None
    return UserProfile(
        email=claims["sub"], name=claims["name"], picture_url=claims.get("picture_url")
    )
