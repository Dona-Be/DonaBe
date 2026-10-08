from fastapi import APIRouter, Request, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse

from src.api.cookies import clear_session_cookies, start_pending_signup, start_session
from src.api.dependencies import (
    CurrentUser,
    CurrentUserIfAny,
    GoogleClientDep,
    PendingSignupProfile,
    UserServiceDep,
)
from src.api.frontend_paths import LOGIN_PATH
from src.core.config import settings
from src.domain.user_profile import UserProfile
from src.models.user import User
from src.schemas.user import PendingSignup, PublicUser, RoleChoice
from src.services.users import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def redirect_with_session(user: User) -> RedirectResponse:
    response = RedirectResponse(settings.frontend_page())
    start_session(response, user)
    return response


def redirect_to_role_choice(profile: UserProfile) -> RedirectResponse:
    response = RedirectResponse(settings.frontend_page(LOGIN_PATH))
    start_pending_signup(response, profile)
    return response


def decide_login_destination(service: UserService, profile: UserProfile) -> Response:
    user = service.identify_on_login(profile)
    if user is None:
        return redirect_to_role_choice(profile)
    return redirect_with_session(user)


@router.get(
    "/login/google",
    status_code=status.HTTP_302_FOUND,
    response_class=RedirectResponse,
    summary="Start the Google login",
    description="Open in the browser, not via fetch: redirects to Google's consent screen.",
)
async def login_with_google(request: Request, google: GoogleClientDep) -> Response:
    callback_path = request.url_for("google_callback").path
    return await google.redirect_to_login(request, settings.frontend_page(callback_path))


@router.get(
    "/callback/google",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    response_class=RedirectResponse,
    summary="Finish the Google login",
    description="Called by Google: sets the right cookie and goes back to the site.",
)
async def google_callback(
    request: Request, google: GoogleClientDep, service: UserServiceDep
) -> Response:
    profile = await google.fetch_profile(request)
    # The database work is synchronous, so keep it off the event loop.
    return await run_in_threadpool(decide_login_destination, service, profile)


@router.get("/pending-signup", response_model=PendingSignup, summary="Read the pending signup")
def read_pending_signup(profile: PendingSignupProfile) -> UserProfile:
    return profile


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=PublicUser,
    summary="Finish the signup by choosing a role",
    description="Creates the user as donor or manager and starts the session.",
)
def sign_up(
    choice: RoleChoice, profile: PendingSignupProfile, service: UserServiceDep, response: Response
) -> User:
    user = service.sign_up(profile, choice.role)
    start_session(response, user)
    return user


@router.get("/me", response_model=PublicUser, summary="Read the current user")
def read_current_user(user: CurrentUser) -> User:
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out from every device",
    description="Invalidates every session of the user and clears the cookies.",
)
def logout(response: Response, user: CurrentUserIfAny, service: UserServiceDep) -> None:
    if user is not None:
        service.logout(user)
    clear_session_cookies(response)
