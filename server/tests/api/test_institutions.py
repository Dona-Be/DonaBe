from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.connectors.companies import company_from
from src.connectors.schemas import Address
from src.models.institution import Institution
from tests.api.helpers import (
    INSTITUTION,
    INSTITUTION_DETAILS,
    INSTITUTION_PREVIEW,
    MY_INSTITUTIONS,
    look_up,
    register,
)
from tests.connectors.samples import AACD, AACD_TAX_ID
from tests.fakes import FakeAddressLookup, FakeCompanyLookup


def test_lookup_previews_the_institution_without_saving_it(
    manager_client: TestClient, companies: FakeCompanyLookup, addresses: FakeAddressLookup
) -> None:
    response = look_up(manager_client, "60.979.457/0001-11")

    assert response.status_code == 200
    assert response.json() == INSTITUTION_PREVIEW
    assert companies.calls == [AACD_TAX_ID]
    assert addresses.calls == []
    assert manager_client.get(MY_INSTITUTIONS).json() == []


def test_registration_fills_the_institution_with_the_official_data(
    manager_client: TestClient, addresses: FakeAddressLookup
) -> None:
    response = register(manager_client, "60.979.457/0001-11")

    assert response.status_code == 201
    assert response.json() == INSTITUTION
    assert addresses.calls == ["04027000"]
    assert manager_client.get(MY_INSTITUTIONS).json() == [INSTITUTION]


def test_registration_saves_the_coordinates_of_the_cep_and_the_cnpj_record(
    manager_client: TestClient, db_session: Session
) -> None:
    register(manager_client)

    saved = select(func.ST_AsText(Institution.location), Institution.cnpj_data)
    location, cnpj_data = db_session.execute(saved).one()

    assert location == "POINT(-46.63611 -23.5475)"
    assert cnpj_data == company_from(AACD_TAX_ID, AACD).raw_data


def test_registration_keeps_what_the_manager_filled_in(
    manager_client: TestClient, addresses: FakeAddressLookup
) -> None:
    response = register(manager_client, **INSTITUTION_DETAILS)

    assert response.json() == {**INSTITUTION, **INSTITUTION_DETAILS}
    assert addresses.calls == ["01310200"]


def test_registration_stores_the_phone_and_the_cep_as_digits(manager_client: TestClient) -> None:
    response = register(manager_client, phone="(11) 99999-0000", postal_code="01310-200")

    assert response.json() == {**INSTITUTION, "phone": "11999990000", "postal_code": "01310200"}


def test_registration_keeps_each_cause_once(manager_client: TestClient) -> None:
    response = register(manager_client, causes=["health", "animals", "health"])

    assert response.json() == {**INSTITUTION, "causes": ["health", "animals"]}


def test_registration_trims_the_texts_and_a_blank_one_counts_as_empty(
    manager_client: TestClient,
) -> None:
    response = register(manager_client, trade_name="   ", number=" 12 ")

    assert response.json() == {**INSTITUTION, "trade_name": None, "number": "12"}


def test_a_cep_without_coordinates_asks_for_a_nearby_cep(
    manager_client: TestClient, addresses: FakeAddressLookup
) -> None:
    addresses.answer = Address(postal_code="04027000", state="SP", city="São Paulo")

    response = register(manager_client)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "O CEP 04027000 não tem uma localização conhecida. Informe um CEP próximo."
    }
    assert manager_client.get(MY_INSTITUTIONS).json() == []


@pytest.mark.parametrize(
    ("field", "value", "detail"),
    [
        ("phone", "(11) 9999-000", "O telefone informado é inválido."),
        ("postal_code", "0131020", "O CEP informado é inválido."),
    ],
)
def test_an_invalid_phone_or_cep_registers_nothing(
    manager_client: TestClient, field: str, value: str, detail: str
) -> None:
    response = register(manager_client, **{field: value})

    assert response.status_code == 422
    assert response.json() == {"detail": detail}
    assert manager_client.get(MY_INSTITUTIONS).json() == []


@pytest.mark.parametrize(
    "details",
    [
        {"legal_name": "Outra razão social"},
        {"causes": ["sports"]},
        {"causes": ["animals"] * 11},
        {"contact_email": "contato"},
        {"website": "javascript:alert(1)"},
        {"instagram": "@exemplo"},
        {"facebook": "exemplo"},
        {"state": "sp"},
        {"street": " "},
        {"description": "x" * 2001},
        {"description": "a\x00b"},
    ],
)
def test_invalid_details_register_nothing(
    manager_client: TestClient, companies: FakeCompanyLookup, details: dict[str, Any]
) -> None:
    assert register(manager_client, **details).status_code == 422
    assert companies.calls == []
    assert manager_client.get(MY_INSTITUTIONS).json() == []
