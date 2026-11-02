import httpx2

from src.connectors.companies import CnpjaCompanyLookup
from src.connectors.json_api import DEFAULT_TIMEOUT
from src.connectors.schemas import Address
from src.domain.charity import RegistryCode, RegistryData
from tests.connectors.fakes import FakeApi
from tests.connectors.helpers import cnpja_company_payload, cnpja_payload
from tests.connectors.samples import AACD, AACD_TAX_ID

AACD_ADDRESS = Address(
    postal_code="04027000",
    state="SP",
    city="São Paulo",
    neighborhood="VL Clementino",
    street="Avenida Prof Ascendino Reis",
    number="724",
    complement=None,
)


def test_get_company_calls_the_default_url_and_returns_the_company(
    fake_api: FakeApi, company_lookup: CnpjaCompanyLookup
) -> None:
    fake_api.response = httpx2.Response(200, json=AACD)

    company = company_lookup.get_company(AACD_TAX_ID)

    assert company.tax_id == AACD_TAX_ID
    assert company.legal_name == "ASSOCIACAO DE ASSISTENCIA A CRIANCA DEFICIENTE"
    assert company.trade_name == "Aacd Ibirapuera"
    assert company.address == AACD_ADDRESS
    assert str(fake_api.requests[0].url) == "https://open.cnpja.com/office/60979457000111"
    assert fake_api.requests[0].extensions["timeout"] == httpx2.Timeout(DEFAULT_TIMEOUT).as_dict()


def test_get_company_builds_the_registry_data_for_the_charity_classifier(
    fake_api: FakeApi, company_lookup: CnpjaCompanyLookup
) -> None:
    fake_api.response = httpx2.Response(200, json=AACD)

    company = company_lookup.get_company(AACD_TAX_ID)

    assert company.registry_data() == RegistryData(
        registration_status="Ativa",
        legal_nature=RegistryCode("3999", "Associação Privada"),
        main_activity=RegistryCode("8630501", "Atividade médica ambulatorial"),
    )


def test_get_company_keeps_the_registry_facts_without_personal_data(
    fake_api: FakeApi, company_lookup: CnpjaCompanyLookup
) -> None:
    fake_api.response = httpx2.Response(200, json=AACD)

    raw_data = company_lookup.get_company(AACD_TAX_ID).raw_data

    assert "phones" not in raw_data
    assert "emails" not in raw_data
    assert "members" not in raw_data["company"]
    assert raw_data["company"]["nature"] == {"id": 3999, "text": "Associação Privada"}
    assert raw_data["status"] == {"id": 2, "text": "Ativa"}
    assert raw_data["address"] == AACD["address"]
    assert "members" in AACD["company"]


def test_get_company_calls_the_configured_url(fake_api: FakeApi) -> None:
    fake_api.response = httpx2.Response(200, json=AACD)
    lookup = CnpjaCompanyLookup(fake_api.client(), base_url="https://cnpj.interno")

    lookup.get_company(AACD_TAX_ID)

    assert str(fake_api.requests[0].url) == "https://cnpj.interno/office/60979457000111"


def test_get_company_accepts_an_alphanumeric_tax_id(
    fake_api: FakeApi, company_lookup: CnpjaCompanyLookup
) -> None:
    fake_api.response = httpx2.Response(200, json=AACD)

    company_lookup.get_company("00000000E08G12")

    assert fake_api.requests[0].url.path == "/office/00000000E08G12"


def test_get_company_keeps_the_leading_zero_of_the_cnae_code(
    fake_api: FakeApi, company_lookup: CnpjaCompanyLookup
) -> None:
    body = cnpja_payload(mainActivity={"id": 111301, "text": "Cultivo de arroz"})
    fake_api.response = httpx2.Response(200, json=body)

    assert company_lookup.get_company(AACD_TAX_ID).main_activity_code == "0111301"


def test_get_company_accepts_codes_sent_as_text(
    fake_api: FakeApi, company_lookup: CnpjaCompanyLookup
) -> None:
    body = cnpja_company_payload(nature={"id": "3999", "text": "Associação Privada"})
    fake_api.response = httpx2.Response(200, json=body)

    assert company_lookup.get_company(AACD_TAX_ID).legal_nature_code == "3999"


def test_get_company_turns_empty_texts_into_none(
    fake_api: FakeApi, company_lookup: CnpjaCompanyLookup
) -> None:
    empty_address = {**AACD["address"], "zip": "", "district": "", "number": "", "details": ""}
    fake_api.response = httpx2.Response(200, json=cnpja_payload(alias="", address=empty_address))

    company = company_lookup.get_company(AACD_TAX_ID)

    assert company.trade_name is None
    assert company.address.postal_code is None
    assert company.address.neighborhood is None
    assert company.address.number is None
    assert company.address.complement is None
