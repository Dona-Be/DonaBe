from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from src.api.cookies import ACCESS_TOKEN_COOKIE, PENDING_SIGNUP_COOKIE
from src.api.dependencies import UserServiceDep
from src.auth.tokens import read_access_token, read_pending_signup_token
from src.domain.user_profile import UserProfile
from src.models.user import Donor, Manager, User

LOGIN_REQUIRED_MESSAGE = "Você precisa entrar para continuar."
NO_PENDING_SIGNUP_MESSAGE = "Nenhum cadastro pendente. Entre com o Google novamente."
ROLE_ALREADY_CHOSEN_MESSAGE = "Você já escolheu o seu papel."
DONORS_ONLY_MESSAGE = "Acesso permitido apenas para doadores."
MANAGERS_ONLY_MESSAGE = "Acesso permitido apenas para gestores."

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


def get_current_donor(user: CurrentUser) -> Donor:
    if not isinstance(user, Donor):
        raise HTTPException(status.HTTP_403_FORBIDDEN, DONORS_ONLY_MESSAGE)
    return user


CurrentDonor = Annotated[Donor, Depends(get_current_donor)]


def get_current_manager(user: CurrentUser) -> Manager:
    if not isinstance(user, Manager):
        raise HTTPException(status.HTTP_403_FORBIDDEN, MANAGERS_ONLY_MESSAGE)
    return user


CurrentManager = Annotated[Manager, Depends(get_current_manager)]


def get_profile_owner(
    user: CurrentUserIfAny, token: PendingSignupCookie = None
) -> User | UserProfile:
    if user is not None:
        return user
    return get_pending_signup_profile(token)


ProfileOwner = Annotated[User | UserProfile, Depends(get_profile_owner)]


def get_new_user_profile(owner: ProfileOwner) -> UserProfile:
    if isinstance(owner, User):
        raise HTTPException(status.HTTP_409_CONFLICT, ROLE_ALREADY_CHOSEN_MESSAGE)
    return owner


NewUserProfile = Annotated[UserProfile, Depends(get_new_user_profile)]
