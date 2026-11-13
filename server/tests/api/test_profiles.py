from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.user import Donor
from tests.api.helpers import (
    ACCESS_TOKEN_COOKIE,
    DONOR_PROFILE,
    DONOR_SIGNUP,
    GOOGLE_CALLBACK,
    MANAGER_PROFILE,
    PENDING_PROFILE,
    cookies_set_by,
    sign_up,
)
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import PAULISTA


def test_donor_signup_creates_the_donor_and_starts_the_session(
    client: TestClient, brasilapi: FakeApi
) -> None:
    response = sign_up(client, "donor", DONOR_SIGNUP)

    assert response.status_code == 201
    assert response.json() == DONOR_PROFILE
    assert "HttpOnly" in cookies_set_by(response)[ACCESS_TOKEN_COOKIE]
    assert str(brasilapi.requests[0].url).endswith("/cep/v2/01310200")
    assert client.get("/api/profiles/me").json() == DONOR_PROFILE


@pytest.mark.usefixtures("brasilapi")
def test_donor_signup_saves_the_coordinates_of_the_cep(
    client: TestClient, db_session: Session
) -> None:
    sign_up(client, "donor", DONOR_SIGNUP)

    location = db_session.scalar(select(func.ST_AsText(Donor.location)))

    assert location == "POINT(-46.63611 -23.5475)"


@pytest.mark.usefixtures("brasilapi")
def test_donor_signup_accepts_an_optional_phone(client: TestClient) -> None:
    response = sign_up(client, "donor", {**DONOR_SIGNUP, "phone": "(11) 99999-0000"})

    assert response.json() == {**DONOR_PROFILE, "phone": "11999990000"}


@pytest.mark.usefixtures("brasilapi")
def test_donor_signup_with_an_invalid_phone_creates_nobody(client: TestClient) -> None:
    response = sign_up(client, "donor", {**DONOR_SIGNUP, "phone": "(11) 9999-000"})

    assert response.status_code == 422
    assert response.json() == {"detail": "O telefone informado é inválido."}
    assert client.get("/api/profiles/me").json() == PENDING_PROFILE


def test_manager_signup_creates_the_manager_and_starts_the_session(client: TestClient) -> None:
    response = sign_up(client, "manager")

    assert response.status_code == 201
    assert response.json() == MANAGER_PROFILE
    assert "HttpOnly" in cookies_set_by(response)[ACCESS_TOKEN_COOKIE]
    assert client.get("/api/profiles/me").json() == MANAGER_PROFILE


@pytest.mark.parametrize(("role", "data"), [("donor", DONOR_SIGNUP), ("manager", None)])
def test_user_with_a_role_cannot_choose_another(
    client: TestClient, brasilapi: FakeApi, role: str, data: dict[str, Any] | None
) -> None:
    sign_up(client, "manager")

    response = client.post(f"/api/profiles/{role}", json=data)

    assert response.status_code == 409
    assert response.json() == {"detail": "Você já escolheu o seu papel."}
    assert brasilapi.requests == []
    assert client.get("/api/profiles/me").json() == MANAGER_PROFILE


def test_signup_without_pending_signup_is_unauthorized(client: TestClient) -> None:
    response = client.post("/api/profiles/manager")

    assert response.status_code == 401
    assert response.json() == {"detail": "Nenhum cadastro pendente. Entre com o Google novamente."}


def test_cep_without_coordinates_asks_for_a_nearby_cep(
    client: TestClient, brasilapi: FakeApi
) -> None:
    brasilapi.response = httpx2.Response(200, json={**PAULISTA, "location": None})

    response = sign_up(client, "donor", DONOR_SIGNUP)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "O CEP 01310200 não tem uma localização conhecida. Informe um CEP próximo."
    }
    assert client.get("/api/profiles/me").json() == PENDING_PROFILE


def test_invalid_cep_is_rejected_before_any_request_is_made(
    client: TestClient, brasilapi: FakeApi
) -> None:
    response = sign_up(client, "donor", {**DONOR_SIGNUP, "postal_code": "0131020"})

    assert response.status_code == 422
    assert response.json() == {"detail": "O CEP informado é inválido."}
    assert brasilapi.requests == []


@pytest.mark.parametrize(
    "data",
    [{**DONOR_SIGNUP, "preferred_causes": ["sports"]}, {"postal_code": "01310-200"}, {}],
    ids=["unknown cause", "no causes", "empty body"],
)
def test_donor_signup_needs_a_cep_and_known_causes(
    client: TestClient, brasilapi: FakeApi, data: dict[str, Any]
) -> None:
    assert sign_up(client, "donor", data).status_code == 422
    assert brasilapi.requests == []


def test_me_of_pending_signup_has_no_role(client: TestClient) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    response = client.get("/api/profiles/me")

    assert response.status_code == 200
    assert response.json() == PENDING_PROFILE


def test_me_without_cookies_is_unauthorized(client: TestClient) -> None:
    response = client.get("/api/profiles/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Nenhum cadastro pendente. Entre com o Google novamente."}
