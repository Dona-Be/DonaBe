from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.user import Donor
from tests.api.helpers import DONOR_PROFILE, DONOR_SIGNUP, GOOGLE_CALLBACK, MANAGER_PROFILE, sign_up
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import ACRELANDIA

ME = "/api/profiles/me"


@pytest.fixture
def donor_client(client: TestClient, brasilapi: FakeApi) -> TestClient:
    sign_up(client, "donor", DONOR_SIGNUP)
    brasilapi.requests.clear()
    return client


def test_donor_edits_name_phone_and_causes_without_checking_the_cep_again(
    donor_client: TestClient, brasilapi: FakeApi
) -> None:
    changes = {"name": "Maria Souza", "phone": "(11) 99999-0000", "preferred_causes": ["elderly"]}
    edited = {**DONOR_PROFILE, **changes, "phone": "11999990000"}

    response = donor_client.patch(ME, json={**changes, "postal_code": "01310200"})

    assert response.status_code == 200
    assert response.json() == edited
    assert donor_client.get(ME).json() == edited
    assert brasilapi.requests == []


def test_a_new_cep_is_checked_and_moves_the_donor(
    donor_client: TestClient, brasilapi: FakeApi, db_session: Session
) -> None:
    brasilapi.response = httpx2.Response(200, json=ACRELANDIA)

    response = donor_client.patch(ME, json={"postal_code": "69945-000"})

    assert response.json() == {**DONOR_PROFILE, "postal_code": "69945000"}
    assert str(brasilapi.requests[0].url).endswith("/cep/v2/69945000")
    location = db_session.scalar(select(func.ST_AsText(Donor.location)))
    assert location == "POINT(-67.055 -10.07387)"


def test_a_new_cep_without_coordinates_keeps_the_old_one(
    donor_client: TestClient, brasilapi: FakeApi
) -> None:
    brasilapi.response = httpx2.Response(200, json={**ACRELANDIA, "location": None})

    response = donor_client.patch(ME, json={"name": "Maria Souza", "postal_code": "69945-000"})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "O CEP 69945000 não tem uma localização conhecida. Informe um CEP próximo."
    }
    assert donor_client.get(ME).json() == DONOR_PROFILE


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 101},
        {"preferred_causes": ["sports"]},
        {"phone": "(11) 9999-000"},
        {"postal_code": "0131020"},
    ],
)
def test_invalid_changes_are_rejected(donor_client: TestClient, changes: dict[str, Any]) -> None:
    response = donor_client.patch(ME, json={"name": "Maria Souza", **changes})

    assert response.status_code == 422
    assert donor_client.get(ME).json() == DONOR_PROFILE


def test_manager_edits_name_and_phone(client: TestClient) -> None:
    sign_up(client, "manager")

    response = client.patch(ME, json={"name": "Maria Souza", "phone": "(11) 2000-0000"})

    assert response.json() == {**MANAGER_PROFILE, "name": "Maria Souza", "phone": "1120000000"}


@pytest.mark.parametrize(
    ("field", "value"), [("postal_code", "01310-200"), ("preferred_causes", ["animals"])]
)
def test_manager_cannot_edit_the_donor_fields(
    client: TestClient, brasilapi: FakeApi, field: str, value: Any
) -> None:
    sign_up(client, "manager")

    response = client.patch(ME, json={"name": "Maria Souza", field: value})

    assert response.status_code == 422
    assert response.json() == {"detail": f"O campo {field} não faz parte do seu perfil."}
    assert brasilapi.requests == []
    assert client.get(ME).json() == MANAGER_PROFILE


@pytest.mark.parametrize("has_pending_signup", [True, False])
def test_only_a_logged_in_user_edits_a_profile(
    client: TestClient, has_pending_signup: bool
) -> None:
    if has_pending_signup:
        client.get(GOOGLE_CALLBACK, follow_redirects=False)

    response = client.patch(ME, json={"name": "Maria Souza"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Você precisa entrar para continuar."}
