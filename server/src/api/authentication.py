from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from src.api.cookies import ACCESS_TOKEN_COOKIE, PENDING_SIGNUP_COOKIE
from src.api.dependencies import UserServiceDep
from src.auth.tokens import read_access_token, read_pending_signup_token
from src.domain.user_profile import UserProfile
from src.models.user import User

LOGIN_REQUIRED_MESSAGE = "Você precisa entrar para continuar."
NO_PENDING_SIGNUP_MESSAGE = "Nenhum cadastro pendente. Entre com o Google novamente."

AccessTokenCookie = Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE)]
PendingSignupCookie = Annotated[str | None, Cookie(alias=PENDING_SIGNUP_COOKIE)]


def unauthorized(message: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, message)


def get_current_user_if_any(
    service: UserServiceDep, token: AccessTokenCookie = None
) -> User | None:
    if token is None:
        return None
    token_session = read_access_token(token)
    if token_session is None:
        return None
    return service.identify_session(token_session.user_id, token_session.session_version)


CurrentUserIfAny = Annotated[User | None, Depends(get_current_user_if_any)]


def get_current_user(user: CurrentUserIfAny) -> User:
    if user is None:
        raise unauthorized(LOGIN_REQUIRED_MESSAGE)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_pending_signup_profile(token: PendingSignupCookie = None) -> UserProfile:
    if token is None:
        raise unauthorized(NO_PENDING_SIGNUP_MESSAGE)
    profile = read_pending_signup_token(token)
    if profile is None:
        raise unauthorized(NO_PENDING_SIGNUP_MESSAGE)
    return profile


PendingSignupProfile = Annotated[UserProfile, Depends(get_pending_signup_profile)]
