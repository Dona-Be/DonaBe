from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.api.helpers import (
    ACCESS_TOKEN_COOKIE,
    GOOGLE_CALLBACK,
    PENDING_SIGNUP_COOKIE,
    cookies_set_by,
    create_donor,
    was_deleted,
)
from tests.fakes import USER_EMAIL


def test_signup_creates_the_user_and_starts_the_session(client: TestClient) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    response = client.post("/api/auth/signup", json={"role": "manager"})

    assert response.status_code == 201
    assert response.json()["role"] == "manager"
    cookies = cookies_set_by(response)
    assert "HttpOnly" in cookies[ACCESS_TOKEN_COOKIE]
    assert was_deleted(cookies[PENDING_SIGNUP_COOKIE])
    assert client.get("/api/auth/me").json()["email"] == USER_EMAIL


def test_signup_without_pending_signup_is_unauthorized(client: TestClient) -> None:
    response = client.post("/api/auth/signup", json={"role": "donor"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Nenhum cadastro pendente. Entre com o Google novamente."}
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
    cookies = cookies_set_by(response)
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
