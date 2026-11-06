from typing import Any

import pytest

from src.connectors.exceptions import ExternalServiceError, RateLimitedError
from src.connectors.schemas import Address, Company
from src.domain.enums import Verdict
from src.domain.exceptions import CnpjNotFoundError, InvalidCnpjError
from src.services.cnpj import CnpjService
from tests.fakes import FakeCompanyLookup

TAX_ID = "60979457000111"
CHARITY_FIELDS: dict[str, Any] = {
    "tax_id": TAX_ID,
    "legal_name": "ASSOCIACAO DE ASSISTENCIA A CRIANCA DEFICIENTE",
    "trade_name": "Aacd Ibirapuera",
    "registration_status": "Ativa",
    "legal_nature_code": "3999",
    "legal_nature_description": "Associação Privada",
    "main_activity_code": "8800600",
    "main_activity_description": "Serviços de assistência social sem alojamento",
    "address": Address(postal_code="04027000", state="SP", city="São Paulo"),
    "raw_data": {"taxId": TAX_ID},
}


def company(**changes: Any) -> Company:
    return Company(**{**CHARITY_FIELDS, **changes})


def test_classify_normalizes_the_cnpj_and_classifies_the_company() -> None:
    companies = FakeCompanyLookup(company())

    result = CnpjService(companies).classify("60.979.457/0001-11")

    assert result.company == company()
    assert result.classification.verdict is Verdict.LIKELY_CHARITY
    assert result.classification.reasons == (
        "OK - Situação cadastral: Ativa",
        "OK - Natureza jurídica: 3999 - Associação Privada",
        "OK - Atividade principal: 8800600 - Serviços de assistência social sem alojamento",
    )
    assert companies.calls == [TAX_ID]


@pytest.mark.parametrize(
    ("changes", "verdict"),
    [
        ({"registration_status": "Baixada"}, Verdict.INACTIVE),
        ({"main_activity_code": "9491000"}, Verdict.NONPROFIT),
        ({"legal_nature_code": "2062"}, Verdict.UNLIKELY),
    ],
    ids=["inactive", "nonprofit", "unlikely"],
)
def test_classify_reports_the_verdict_of_the_charity_classifier(
    changes: dict[str, str], verdict: Verdict
) -> None:
    result = CnpjService(FakeCompanyLookup(company(**changes))).classify(TAX_ID)

    assert result.classification.verdict is verdict


def test_classify_rejects_an_invalid_cnpj_without_calling_the_lookup() -> None:
    companies = FakeCompanyLookup(company())
    service = CnpjService(companies)

    with pytest.raises(InvalidCnpjError):
        service.classify("60979457000110")

    assert companies.calls == []


@pytest.mark.parametrize(
    "error",
    [CnpjNotFoundError(TAX_ID), RateLimitedError("limit"), ExternalServiceError("down")],
    ids=["not found", "rate limited", "external failure"],
)
def test_classify_propagates_the_lookup_errors(error: Exception) -> None:
    service = CnpjService(FakeCompanyLookup(error))
    expected = type(error)

    with pytest.raises(expected):
        service.classify(TAX_ID)
