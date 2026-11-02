import httpx2
import pytest
from pydantic import ValidationError

from src.connectors.exceptions import ExternalServiceError, RateLimitedError
from src.domain.exceptions import CnpjNotFoundError, InvalidCnpjError
from tests.connectors.helpers import (
    cnpja_address_payload,
    cnpja_company_payload,
    cnpja_payload,
    company_lookup_with,
)
from tests.connectors.samples import (
    AACD,
    AACD_TAX_ID,
    CNPJ_INVALID,
    CNPJ_NOT_FOUND,
    CNPJ_RATE_LIMITED,
)
from tests.helpers import fullwidth


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
    lookup, api = company_lookup_with(httpx2.Response(200, json=AACD))

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
        (httpx2.Response(200, json=cnpja_payload(company=None)), ExternalServiceError),
        (httpx2.Response(200, json=cnpja_payload(status={})), ExternalServiceError),
        (httpx2.Response(200, json=cnpja_payload(status={"text": None})), ExternalServiceError),
        (httpx2.Response(200, json=cnpja_payload(status={"text": ""})), ExternalServiceError),
        (
            httpx2.Response(200, json=cnpja_company_payload(nature={"id": 3999})),
            ExternalServiceError,
        ),
        (
            httpx2.Response(200, json=cnpja_company_payload(nature={"id": None, "text": "x"})),
            ExternalServiceError,
        ),
        (
            httpx2.Response(200, json=cnpja_company_payload(nature={"id": True, "text": "x"})),
            ExternalServiceError,
        ),
        (
            httpx2.Response(200, json=cnpja_payload(mainActivity={"id": 8630501})),
            ExternalServiceError,
        ),
        (httpx2.Response(200, json=cnpja_address_payload(state="sp")), ExternalServiceError),
        (
            httpx2.Response(200, json=cnpja_address_payload(zip=fullwidth("04027000"))),
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
    lookup, _ = company_lookup_with(response)

    with pytest.raises(error):
        lookup.get_company(AACD_TAX_ID)


def test_get_company_names_the_tax_id_that_was_not_found() -> None:
    lookup, _ = company_lookup_with(httpx2.Response(404, json=CNPJ_NOT_FOUND))

    with pytest.raises(CnpjNotFoundError, match=AACD_TAX_ID):
        lookup.get_company(AACD_TAX_ID)


def test_get_company_keeps_the_validation_error_as_the_cause() -> None:
    body = cnpja_address_payload(zip="7004091")
    lookup, _ = company_lookup_with(httpx2.Response(200, json=body))

    with pytest.raises(ExternalServiceError) as caught:
        lookup.get_company(AACD_TAX_ID)

    assert caught.value.log_message == "CNPJá sent an unexpected body"
    assert isinstance(caught.value.__cause__, ValidationError)
