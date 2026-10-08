from datetime import timedelta

from fastapi import Response

from src.auth.tokens import (
    ACCESS_TOKEN_LIFETIME,
    PENDING_SIGNUP_LIFETIME,
    issue_access_token,
    issue_pending_signup_token,
)
from src.core.config import settings
from src.domain.user_profile import UserProfile
from src.models.user import User

ACCESS_TOKEN_COOKIE = "access_token"
PENDING_SIGNUP_COOKIE = "pending_signup"
COOKIE_SECURITY = {"httponly": True, "secure": settings.is_production, "samesite": "lax"}


def set_cookie(response: Response, name: str, value: str, lifetime: timedelta) -> None:
    response.set_cookie(name, value, max_age=int(lifetime.total_seconds()), **COOKIE_SECURITY)


def delete_cookie(response: Response, name: str) -> None:
    response.delete_cookie(name, **COOKIE_SECURITY)


def start_session(response: Response, user: User) -> None:
    token = issue_access_token(user.id, user.session_version)
    set_cookie(response, ACCESS_TOKEN_COOKIE, token, ACCESS_TOKEN_LIFETIME)
    delete_cookie(response, PENDING_SIGNUP_COOKIE)


def start_pending_signup(response: Response, profile: UserProfile) -> None:
    token = issue_pending_signup_token(profile)
    set_cookie(response, PENDING_SIGNUP_COOKIE, token, PENDING_SIGNUP_LIFETIME)
    delete_cookie(response, ACCESS_TOKEN_COOKIE)


def clear_session_cookies(response: Response) -> None:
    delete_cookie(response, ACCESS_TOKEN_COOKIE)
    delete_cookie(response, PENDING_SIGNUP_COOKIE)
