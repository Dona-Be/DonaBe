from typing import Any

import httpx2
import pytest
from pydantic import ValidationError

from src.connectors.companies import CnpjaCompanyLookup
from src.connectors.exceptions import ExternalServiceError, RateLimitedError
from src.connectors.json_api import DEFAULT_TIMEOUT
from src.connectors.schemas import Address
from src.domain.charity import RegistryCode, RegistryData
from src.domain.exceptions import CnpjNotFoundError, InvalidCnpjError
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import AACD, CNPJ_INVALID, CNPJ_NOT_FOUND, CNPJ_RATE_LIMITED
from tests.helpers import fullwidth

TAX_ID = "60979457000111"
AACD_ADDRESS = Address(
    postal_code="04027000",
    state="SP",
    city="São Paulo",
    neighborhood="VL Clementino",
    street="Avenida Prof Ascendino Reis",
    number="724",
    complement=None,
)


def payload(**changes: Any) -> dict[str, Any]:
    return {**AACD, **changes}


def company_payload(**changes: Any) -> dict[str, Any]:
    return payload(company={**AACD["company"], **changes})


def address_payload(**changes: Any) -> dict[str, Any]:
    return payload(address={**AACD["address"], **changes})


def lookup_with(
    response: httpx2.Response | Exception, **options: str
) -> tuple[CnpjaCompanyLookup, FakeApi]:
    api = FakeApi(response)
    return CnpjaCompanyLookup(api.client(), **options), api


def test_get_company_calls_the_default_url_and_returns_the_company() -> None:
    lookup, api = lookup_with(httpx2.Response(200, json=AACD))

    company = lookup.get_company(TAX_ID)

    assert company.tax_id == TAX_ID
    assert company.legal_name == "ASSOCIACAO DE ASSISTENCIA A CRIANCA DEFICIENTE"
    assert company.trade_name == "Aacd Ibirapuera"
    assert company.address == AACD_ADDRESS
    assert str(api.requests[0].url) == "https://open.cnpja.com/office/60979457000111"
    assert api.requests[0].extensions["timeout"] == httpx2.Timeout(DEFAULT_TIMEOUT).as_dict()


def test_get_company_builds_the_registry_data_for_the_charity_classifier() -> None:
    lookup, _ = lookup_with(httpx2.Response(200, json=AACD))

    company = lookup.get_company(TAX_ID)

    assert company.registry_data() == RegistryData(
        registration_status="Ativa",
        legal_nature=RegistryCode("3999", "Associação Privada"),
        main_activity=RegistryCode("8630501", "Atividade médica ambulatorial"),
    )


def test_get_company_keeps_the_registry_facts_without_personal_data() -> None:
    lookup, _ = lookup_with(httpx2.Response(200, json=AACD))

    raw_data = lookup.get_company(TAX_ID).raw_data

    assert "phones" not in raw_data
    assert "emails" not in raw_data
    assert "members" not in raw_data["company"]
    assert raw_data["company"]["nature"] == {"id": 3999, "text": "Associação Privada"}
    assert raw_data["status"] == {"id": 2, "text": "Ativa"}
    assert raw_data["address"] == AACD["address"]
    assert "members" in AACD["company"]


def test_get_company_calls_the_configured_url() -> None:
    lookup, api = lookup_with(httpx2.Response(200, json=AACD), base_url="https://cnpj.interno")

    lookup.get_company(TAX_ID)

    assert str(api.requests[0].url) == "https://cnpj.interno/office/60979457000111"


def test_get_company_accepts_an_alphanumeric_tax_id() -> None:
    lookup, api = lookup_with(httpx2.Response(200, json=AACD))

    lookup.get_company("00000000E08G12")

    assert api.requests[0].url.path == "/office/00000000E08G12"


def test_get_company_keeps_the_leading_zero_of_the_cnae_code() -> None:
    activity = {"id": 111301, "text": "Cultivo de arroz"}
    lookup, _ = lookup_with(httpx2.Response(200, json=payload(mainActivity=activity)))

    assert lookup.get_company(TAX_ID).main_activity_code == "0111301"


def test_get_company_accepts_codes_sent_as_text() -> None:
    nature = {"id": "3999", "text": "Associação Privada"}
    lookup, _ = lookup_with(httpx2.Response(200, json=company_payload(nature=nature)))

    assert lookup.get_company(TAX_ID).legal_nature_code == "3999"


def test_get_company_turns_empty_texts_into_none() -> None:
    empty_address = {**AACD["address"], "zip": "", "district": "", "number": "", "details": ""}
    lookup, _ = lookup_with(httpx2.Response(200, json=payload(alias="", address=empty_address)))

    company = lookup.get_company(TAX_ID)

    assert company.trade_name is None
    assert company.address.postal_code is None
    assert company.address.neighborhood is None
    assert company.address.number is None
    assert company.address.complement is None


@pytest.mark.parametrize(
    "tax_id",
    [
        "",
        "../saude",
        "60979457000111?x=1",
        "60.979.457/0001-11",
        "00000000e08g12",
        "6097945700011",
        "609794570001111",
        "0000000000019A",
        fullwidth("60979457000111"),
    ],
    ids=[
        "empty",
        "path",
        "query",
        "punctuated",
        "lower case",
        "13 characters",
        "15 characters",
        "letter in the check digit",
        "non ascii digits",
    ],
)
def test_get_company_only_accepts_the_tax_id_the_service_normalized(tax_id: str) -> None:
    lookup, api = lookup_with(httpx2.Response(200, json=AACD))

    with pytest.raises(InvalidCnpjError):
        lookup.get_company(tax_id)

    assert api.requests == []


@pytest.mark.parametrize(
    ("response", "error"),
    [
        (httpx2.Response(400, json=CNPJ_INVALID), InvalidCnpjError),
        (httpx2.Response(404, json=CNPJ_NOT_FOUND), CnpjNotFoundError),
        (httpx2.Response(429, json=CNPJ_RATE_LIMITED), RateLimitedError),
        (httpx2.Response(429, text="<html>Too Many Requests</html>"), RateLimitedError),
        (httpx2.Response(500, text="Internal Server Error"), ExternalServiceError),
        (httpx2.Response(203, json=AACD), ExternalServiceError),
        (httpx2.Response(200, json=[]), ExternalServiceError),
        (httpx2.Response(200, json=payload(company=None)), ExternalServiceError),
        (httpx2.Response(200, json=payload(status={})), ExternalServiceError),
        (httpx2.Response(200, json=payload(status={"text": None})), ExternalServiceError),
        (httpx2.Response(200, json=payload(status={"text": ""})), ExternalServiceError),
        (httpx2.Response(200, json=company_payload(nature={"id": 3999})), ExternalServiceError),
        (
            httpx2.Response(200, json=company_payload(nature={"id": None, "text": "x"})),
            ExternalServiceError,
        ),
        (
            httpx2.Response(200, json=company_payload(nature={"id": True, "text": "x"})),
            ExternalServiceError,
        ),
        (httpx2.Response(200, json=payload(mainActivity={"id": 8630501})), ExternalServiceError),
        (httpx2.Response(200, json=address_payload(state="sp")), ExternalServiceError),
        (
            httpx2.Response(200, json=address_payload(zip=fullwidth("04027000"))),
            ExternalServiceError,
        ),
        (httpx2.ConnectError("no network"), ExternalServiceError),
    ],
    ids=[
        "400",
        "404",
        "429",
        "429 without json",
        "500 without json",
        "203 with company",
        "list",
        "without company",
        "without status",
        "null status text",
        "empty status text",
        "nature without text",
        "null nature id",
        "boolean nature id",
        "activity without text",
        "lower case state",
        "non ascii zip",
        "network",
    ],
)
def test_get_company_maps_failures(
    response: httpx2.Response | Exception, error: type[Exception]
) -> None:
    lookup, _ = lookup_with(response)

    with pytest.raises(error):
        lookup.get_company(TAX_ID)


def test_get_company_names_the_tax_id_that_was_not_found() -> None:
    lookup, _ = lookup_with(httpx2.Response(404, json=CNPJ_NOT_FOUND))

    with pytest.raises(CnpjNotFoundError, match=TAX_ID):
        lookup.get_company(TAX_ID)


def test_get_company_keeps_the_validation_error_as_the_cause() -> None:
    lookup, _ = lookup_with(httpx2.Response(200, json=address_payload(zip="7004091")))

    with pytest.raises(ExternalServiceError) as caught:
        lookup.get_company(TAX_ID)

    assert caught.value.log_message == "CNPJá sent an unexpected body"
    assert isinstance(caught.value.__cause__, ValidationError)
