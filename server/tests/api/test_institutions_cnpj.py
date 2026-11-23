from collections.abc import Callable

import httpx2
import pytest
from fastapi.testclient import TestClient

from src.connectors.companies import company_from
from src.connectors.exceptions import ExternalServiceError
from src.connectors.schemas import Company
from src.domain.exceptions import CnpjNotFoundError
from tests.api.helpers import (
    INSTITUTION,
    INSTITUTION_PREVIEW,
    MY_INSTITUTIONS,
    look_up,
    register,
)
from tests.connectors.samples import AACD, AACD_TAX_ID
from tests.fakes import FakeCompanyLookup

LIMITED = {"id": 2062, "text": "Sociedade Empresária Limitada"}
INACTIVE_COMPANY = company_from(AACD_TAX_ID, {**AACD, "status": {"text": "Baixada"}})
LIMITED_COMPANY = company_from(
    AACD_TAX_ID, {**AACD, "company": {**AACD["company"], "nature": LIMITED}}
)
Attempt = Callable[..., httpx2.Response]


@pytest.mark.parametrize("attempt", [look_up, register])
@pytest.mark.parametrize(
    ("answer", "refusal"),
    [
        (
            CnpjNotFoundError(AACD_TAX_ID),
            (404, "Nenhuma empresa encontrada com o CNPJ 60979457000111."),
        ),
        (INACTIVE_COMPANY, (422, "Não é possível cadastrar um CNPJ que não está ativo.")),
        (
            LIMITED_COMPANY,
            (
                422,
                "Não é possível cadastrar instituições com a natureza jurídica "
                "2062 - Sociedade Empresária Limitada.",
            ),
        ),
        (
            ExternalServiceError("CNPJá is down"),
            (503, "Um serviço externo não respondeu. Tente novamente em alguns minutos."),
        ),
    ],
    ids=["not found", "inactive", "unsupported legal nature", "external failure"],
)
def test_a_cnpj_that_cannot_be_registered_is_refused(
    manager_client: TestClient,
    companies: FakeCompanyLookup,
    attempt: Attempt,
    answer: Company | Exception,
    refusal: tuple[int, str],
) -> None:
    companies.answer = answer
    status, detail = refusal

    response = attempt(manager_client)

    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert manager_client.get(MY_INSTITUTIONS).json() == []


@pytest.mark.parametrize("attempt", [look_up, register])
def test_an_invalid_cnpj_is_refused_before_any_request_is_made(
    manager_client: TestClient, companies: FakeCompanyLookup, attempt: Attempt
) -> None:
    response = attempt(manager_client, "60.979.457/0001-10")

    assert response.status_code == 422
    assert response.json() == {"detail": "O CNPJ informado é inválido."}
    assert companies.calls == []


@pytest.mark.parametrize("attempt", [look_up, register])
def test_a_cnpj_already_registered_is_refused_before_any_request_is_made(
    manager_client: TestClient, companies: FakeCompanyLookup, attempt: Attempt
) -> None:
    register(manager_client)
    companies.calls.clear()

    response = attempt(manager_client, "60.979.457/0001-11")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Já existe uma instituição cadastrada com o CNPJ 60979457000111."
    }
    assert companies.calls == []
    assert manager_client.get(MY_INSTITUTIONS).json() == [INSTITUTION]


@pytest.mark.parametrize(
    ("missing", "field", "filled_in"),
    [
        ("street", "street", "Rua A"),
        ("number", "number", "S/N"),
        ("district", "neighborhood", "Centro"),
        ("zip", "postal_code", "01310200"),
    ],
)
def test_an_address_part_missing_in_the_cnpj_must_be_filled_in_by_the_manager(
    manager_client: TestClient,
    companies: FakeCompanyLookup,
    missing: str,
    field: str,
    filled_in: str,
) -> None:
    address = {**AACD["address"], missing: ""}
    companies.answer = company_from(AACD_TAX_ID, {**AACD, "address": address})

    preview = look_up(manager_client)
    refused = register(manager_client)
    accepted = register(manager_client, **{field: filled_in})

    assert preview.json() == {**INSTITUTION_PREVIEW, field: None}
    assert refused.status_code == 422
    assert refused.json() == {
        "detail": "O endereço do CNPJ está incompleto. Informe rua, número, bairro e CEP."
    }
    assert accepted.json() == {**INSTITUTION, field: filled_in}


@pytest.mark.parametrize(
    ("nature", "institution_type"),
    [
        ({"id": 3069, "text": "Fundação Privada"}, "foundation"),
        ({"id": 3220, "text": "Organização Religiosa"}, "religious_organization"),
    ],
)
def test_the_legal_nature_decides_the_type_of_the_institution(
    manager_client: TestClient,
    companies: FakeCompanyLookup,
    nature: dict[str, int | str],
    institution_type: str,
) -> None:
    company = {**AACD["company"], "nature": nature}
    companies.answer = company_from(AACD_TAX_ID, {**AACD, "company": company})

    register(manager_client)

    assert manager_client.get(MY_INSTITUTIONS).json()[0]["type"] == institution_type
