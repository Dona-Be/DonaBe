import httpx2
from sqlalchemy.orm import Session

from src.api.frontend_paths import LOGIN_FAILED_PATH, LOGIN_PATH
from src.core.config import settings
from src.domain.user_profile import UserProfile
from src.models.user import Donor
from tests.fakes import USER_EMAIL, USER_NAME

SITE_URL = settings.frontend_page()
LOGIN_URL = settings.frontend_page(LOGIN_PATH)
LOGIN_FAILED_URL = settings.frontend_page(LOGIN_FAILED_PATH)
GOOGLE_CALLBACK = "/api/auth/callback/google"
ACCESS_TOKEN_COOKIE = "access_token"
PENDING_SIGNUP_COOKIE = "pending_signup"


def create_donor(db_session: Session, email: str = USER_EMAIL) -> Donor:
    donor = Donor.from_profile(UserProfile(email=email, name=USER_NAME, picture_url=None))
    db_session.add(donor)
    db_session.commit()
    return donor


def cookies_set_by(response: httpx2.Response) -> dict[str, str]:
    return {header.split("=", 1)[0]: header for header in response.headers.get_list("set-cookie")}


def was_deleted(cookie_header: str) -> bool:
    return "Max-Age=0" in cookie_header
