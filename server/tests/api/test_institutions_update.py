from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.connectors.addresses import address_from
from src.connectors.schemas import Address
from src.models.institution import Institution
from tests.api.helpers import (
    INSTITUTION,
    INSTITUTION_DETAILS,
    INSTITUTIONS,
    MY_INSTITUTIONS,
    OPTIONAL_DETAILS,
    register,
)
from tests.connectors.samples import ACRELANDIA
from tests.fakes import FakeAddressLookup
from tests.models.helpers import save_need

OWN = f"{INSTITUTIONS}/1"


@pytest.fixture
def owner_client(manager_client: TestClient, addresses: FakeAddressLookup) -> TestClient:
    register(manager_client)
    addresses.calls.clear()
    return manager_client


def test_the_manager_edits_their_own_institution(
    owner_client: TestClient, addresses: FakeAddressLookup
) -> None:
    edited = {**INSTITUTION, **INSTITUTION_DETAILS}

    response = owner_client.patch(OWN, json=INSTITUTION_DETAILS)

    assert response.status_code == 200
    assert response.json() == edited
    assert owner_client.get(MY_INSTITUTIONS).json() == [edited]
    assert addresses.calls == ["01310200"]


def test_a_new_cep_moves_the_institution(
    owner_client: TestClient, addresses: FakeAddressLookup, db_session: Session
) -> None:
    addresses.answer = address_from(ACRELANDIA)

    response = owner_client.patch(OWN, json={"postal_code": "69945-000"})

    assert response.json() == {**INSTITUTION, "postal_code": "69945000"}
    location = db_session.scalar(select(func.ST_AsText(Institution.location)))
    assert location == "POINT(-67.055 -10.07387)"


def test_the_same_cep_is_not_looked_up_again(
    owner_client: TestClient, addresses: FakeAddressLookup
) -> None:
    response = owner_client.patch(OWN, json={"postal_code": "04027-000", "number": "725"})

    assert response.json() == {**INSTITUTION, "number": "725"}
    assert addresses.calls == []


def test_a_new_cep_without_coordinates_keeps_the_old_one(
    owner_client: TestClient, addresses: FakeAddressLookup
) -> None:
    addresses.answer = Address(postal_code="69945000", state="AC", city="Acrelândia")

    response = owner_client.patch(OWN, json={"number": "725", "postal_code": "69945-000"})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "O CEP 69945000 não tem uma localização conhecida. Informe um CEP próximo."
    }
    assert owner_client.get(MY_INSTITUTIONS).json() == [INSTITUTION]


def test_an_empty_text_removes_an_optional_field(owner_client: TestClient) -> None:
    owner_client.patch(OWN, json=OPTIONAL_DETAILS)

    response = owner_client.patch(OWN, json=dict.fromkeys(OPTIONAL_DETAILS, ""))

    assert response.json() == {**INSTITUTION, **dict.fromkeys(OPTIONAL_DETAILS)}


def test_a_null_keeps_the_saved_value(owner_client: TestClient) -> None:
    owner_client.patch(OWN, json=INSTITUTION_DETAILS)

    response = owner_client.patch(OWN, json=dict.fromkeys(INSTITUTION_DETAILS))

    assert response.json() == {**INSTITUTION, **INSTITUTION_DETAILS}


@pytest.mark.parametrize(
    "changes",
    [
        {"cnpj": "11222333000181"},
        {"legal_name": "Outra razão social"},
        {"phone": "(11) 9999-000"},
        {"postal_code": "0131020"},
        {"contact_email": "contato"},
        {"website": "javascript:alert(1)"},
        {"state": "São Paulo"},
        {"city": ""},
        {"number": ""},
        {"neighborhood": " "},
        {"trade_name": "x" * 201},
        {"trade_name": "\x00"},
    ],
)
def test_invalid_changes_are_rejected(owner_client: TestClient, changes: dict[str, Any]) -> None:
    response = owner_client.patch(OWN, json={"description": "Nova descrição", **changes})

    assert response.status_code == 422
    assert owner_client.get(MY_INSTITUTIONS).json() == [INSTITUTION]


def test_another_manager_cannot_edit_the_institution(
    manager_client: TestClient, db_session: Session
) -> None:
    institution = save_need(db_session).institution

    response = manager_client.patch(f"{INSTITUTIONS}/{institution.id}", json={"number": "1"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Apenas o gestor da instituição pode editá-la."}
    db_session.refresh(institution)
    assert institution.number == "1000"


def test_an_institution_that_does_not_exist_cannot_be_edited(manager_client: TestClient) -> None:
    response = manager_client.patch(f"{INSTITUTIONS}/1", json={"number": "1"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Instituição não encontrada."}
