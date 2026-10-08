from collections.abc import Generator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.cookies import ACCESS_TOKEN_COOKIE, PENDING_SIGNUP_COOKIE
from src.auth.google import GoogleClient, google_client
from src.auth.tokens import read_access_token, read_pending_signup_token
from src.core.database import engine
from src.domain.user_profile import UserProfile
from src.models.user import User
from src.repositories.users import SqlAlchemyUserRepository, UserRepository
from src.services.users import UserService


def get_db_session() -> Generator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session


def get_google_client() -> GoogleClient:
    return google_client


def get_user_repository(session: Annotated[Session, Depends(get_db_session)]) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repository)


GoogleClientDep = Annotated[GoogleClient, Depends(get_google_client)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AccessTokenCookie = Annotated[str | None, Cookie(alias=ACCESS_TOKEN_COOKIE)]
PendingSignupCookie = Annotated[str | None, Cookie(alias=PENDING_SIGNUP_COOKIE)]


def unauthorized(message: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, message)


def get_current_user_if_any(
    service: UserServiceDep, token: AccessTokenCookie = None
) -> User | None:
    session = None if token is None else read_access_token(token)
    if session is None:
        return None
    return service.identify_session(session.user_id, session.session_version)


CurrentUserIfAny = Annotated[User | None, Depends(get_current_user_if_any)]


def get_current_user(user: CurrentUserIfAny) -> User:
    if user is None:
        raise unauthorized("Você precisa entrar para continuar.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_pending_signup_profile(token: PendingSignupCookie = None) -> UserProfile:
    profile = None if token is None else read_pending_signup_token(token)
    if profile is None:
        raise unauthorized("Nenhum cadastro pendente. Entre com o Google novamente.")
    return profile


PendingSignupProfile = Annotated[UserProfile, Depends(get_pending_signup_profile)]
