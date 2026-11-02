import httpx2
import pytest
from authlib.integrations.starlette_client import OAuthError
from fastapi.testclient import TestClient

from src.models.user import Donor
from tests.api.helpers import (
    ACCESS_TOKEN_COOKIE,
    GOOGLE_CALLBACK,
    LOGIN_FAILED_URL,
    LOGIN_URL,
    PENDING_SIGNUP_COOKIE,
    SITE_URL,
    cookies_set_by,
    was_deleted,
)
from tests.fakes import USER_EMAIL, USER_NAME, USER_PICTURE, FakeGoogleApp, google_token


def test_login_redirects_to_google_with_the_frontend_callback(client: TestClient) -> None:
    response = client.get("/api/auth/login/google", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"].endswith(f"redirect_uri={SITE_URL}{GOOGLE_CALLBACK}")


def test_login_that_cannot_reach_google_goes_back_to_login(
    client: TestClient, fake_google: FakeGoogleApp
) -> None:
    fake_google.error = httpx2.ConnectError("metadata unreachable")

    response = client.get("/api/auth/login/google", follow_redirects=False)

    assert response.headers["location"] == LOGIN_FAILED_URL


def test_callback_of_known_user_starts_the_session(client: TestClient, donor: Donor) -> None:
    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == SITE_URL
    assert "HttpOnly" in cookies_set_by(response)[ACCESS_TOKEN_COOKIE]
    assert client.get("/api/auth/me").json() == {
        "id": donor.id,
        "email": USER_EMAIL,
        "name": USER_NAME,
        "picture_url": None,
        "role": "donor",
    }


def test_callback_of_new_user_starts_a_pending_signup(client: TestClient) -> None:
    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == LOGIN_URL
    cookies = cookies_set_by(response)
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


def test_callback_with_google_failure_goes_back_to_login_and_logs_the_cause(
    client: TestClient, fake_google: FakeGoogleApp, caplog: pytest.LogCaptureFixture
) -> None:
    fake_google.error = OAuthError(error="access_denied")

    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == LOGIN_FAILED_URL
    assert cookies_set_by(response) == {}
    assert "Google login failed" in caplog.text
    assert "access_denied" in caplog.text


def test_google_failure_log_keeps_the_cause_on_one_line(
    client: TestClient, fake_google: FakeGoogleApp, caplog: pytest.LogCaptureFixture
) -> None:
    fake_google.error = OAuthError(error="access_denied", description="forged\nINFO: fake line")

    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert "forged\\nINFO: fake line" in caplog.text
    assert "\nINFO: fake line" not in caplog.text


def test_callback_with_unverified_email_goes_back_to_login(
    client: TestClient, fake_google: FakeGoogleApp
) -> None:
    fake_google.token = {"userinfo": {"email": USER_EMAIL, "email_verified": False}}

    response = client.get(GOOGLE_CALLBACK, follow_redirects=False)

    assert response.headers["location"] == LOGIN_FAILED_URL
