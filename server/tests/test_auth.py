import httpx2
from authlib.integrations.starlette_client import OAuthError
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.user_profile import UserProfile
from src.models.user import Donor
from tests.fakes import USER_EMAIL, USER_NAME, USER_PICTURE, FakeGoogleApp, google_token

FRONTEND_URL = "http://localhost:5173"
LOGIN_FAILED_URL = f"{FRONTEND_URL}/login?error=login_failed"
GOOGLE_CALLBACK = "/api/auth/callback/google"
ACCESS_TOKEN_COOKIE = "access_token"
PENDING_SIGNUP_COOKIE = "pending_signup"


def create_donor(db_session: Session, email: str = USER_EMAIL) -> Donor:
    donor = Donor.from_profile(UserProfile(email=email, name=USER_NAME, picture_url=None))
    db_session.add(donor)
    db_session.commit()
    return donor


def set_cookies(response: httpx2.Response) -> dict[str, str]:
    return {header.split("=", 1)[0]: header for header in response.headers.get_list("set-cookie")}


def was_deleted(cookie_header: str) -> bool:
    return "Max-Age=0" in cookie_header


def test_login_redirects_to_google_with_the_frontend_callback(client: TestClient) -> None:
    response = client.get("/api/auth/login/google", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"].endswith(f"redirect_uri={FRONTEND_URL}{GOOGLE_CALLBACK}")


def test_login_that_cannot_reach_google_goes_back_to_login(
    client: TestClient, fake_google: FakeGoogleApp
) -> None:
    fake_google.error = httpx2.ConnectError("metadata unreachable")

    response = client.get("/api/auth/login/google", follow_redirects=False)

    assert response.headers["location"] == LOGIN_FAILED_URL


def test_callback_of_known_user_starts_the_session(client: TestClient, db_session: Session) -> None:
    donor = create_donor(db_session)

    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == FRONTEND_URL
    assert "HttpOnly" in set_cookies(response)[ACCESS_TOKEN_COOKIE]
    assert client.get("/api/auth/me").json() == {
        "id": donor.id,
        "email": USER_EMAIL,
        "name": USER_NAME,
        "picture_url": None,
        "role": "donor",
    }


def test_callback_of_new_user_starts_a_pending_signup(client: TestClient) -> None:
    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == f"{FRONTEND_URL}/login"
    cookies = set_cookies(response)
    assert "HttpOnly" in cookies[PENDING_SIGNUP_COOKIE]
    assert was_deleted(cookies[ACCESS_TOKEN_COOKIE])
    assert client.get("/api/auth/pending-signup").json() == {
        "email": USER_EMAIL,
        "name": USER_NAME,
        "picture_url": USER_PICTURE,
    }
    assert client.get("/api/auth/me").status_code == 401


def test_callback_lowercases_the_google_email(
    client: TestClient, fake_google: FakeGoogleApp
) -> None:
    fake_google.token = google_token("Maria@Exemplo.com")

    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert client.get("/api/auth/pending-signup").json()["email"] == USER_EMAIL
    assert client.post("/api/auth/signup", json={"role": "donor"}).json()["email"] == USER_EMAIL


def test_callback_with_google_failure_goes_back_to_login(
    client: TestClient, fake_google: FakeGoogleApp
) -> None:
    fake_google.error = OAuthError(error="access_denied")

    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == LOGIN_FAILED_URL
    assert set_cookies(response) == {}


def test_callback_with_unverified_email_goes_back_to_login(
    client: TestClient, fake_google: FakeGoogleApp
) -> None:
    fake_google.token = {"userinfo": {"email": USER_EMAIL, "email_verified": False}}

    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == LOGIN_FAILED_URL


def test_signup_creates_the_user_and_starts_the_session(client: TestClient) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    response = client.post("/api/auth/signup", json={"role": "manager"})

    assert response.status_code == 201
    assert response.json()["role"] == "manager"
    cookies = set_cookies(response)
    assert "HttpOnly" in cookies[ACCESS_TOKEN_COOKIE]
    assert was_deleted(cookies[PENDING_SIGNUP_COOKIE])
    assert client.get("/api/auth/me").json()["email"] == USER_EMAIL


def test_signup_without_pending_signup_is_unauthorized(client: TestClient) -> None:
    response = client.post("/api/auth/signup", json={"role": "donor"})

    assert response.status_code == 401
    assert client.get("/api/auth/pending-signup").status_code == 401


def test_signup_with_unknown_role_is_invalid(client: TestClient) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert client.post("/api/auth/signup", json={"role": "boss"}).status_code == 422


def test_signup_of_existing_email_conflicts(client: TestClient, db_session: Session) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    create_donor(db_session)

    response = client.post("/api/auth/signup", json={"role": "donor"})

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Já existe um usuário cadastrado com o e-mail maria@exemplo.com."
    }


def test_me_without_cookie_is_unauthorized(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Você precisa entrar para continuar."}


def test_me_with_tampered_cookie_is_unauthorized(client: TestClient) -> None:
    client.cookies.set(ACCESS_TOKEN_COOKIE, "tampered")

    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_the_cookies_and_invalidates_other_devices(
    client: TestClient, db_session: Session
) -> None:
    create_donor(db_session)
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    other_device_token = client.cookies[ACCESS_TOKEN_COOKIE]

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    cookies = set_cookies(response)
    assert was_deleted(cookies[ACCESS_TOKEN_COOKIE])
    assert was_deleted(cookies[PENDING_SIGNUP_COOKIE])
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set(ACCESS_TOKEN_COOKIE, other_device_token)
    assert client.get("/api/auth/me").status_code == 401


def test_login_after_logout_starts_a_fresh_session(client: TestClient, db_session: Session) -> None:
    create_donor(db_session)
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    client.post("/api/auth/logout")

    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert client.get("/api/auth/me").status_code == 200


def test_logout_without_session_still_succeeds(client: TestClient) -> None:
    assert client.post("/api/auth/logout").status_code == 204
