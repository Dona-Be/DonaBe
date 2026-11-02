from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import httpx2

from src.connectors.exceptions import ExternalServiceError
from src.connectors.json_api import get_bytes, parse_json
from src.connectors.schemas import MALFORMED_BODY_ERRORS, Address, Company
from src.domain.cnpj import TAX_ID_PATTERN
from src.domain.exceptions import CnpjNotFoundError, InvalidCnpjError

CNPJA_URL = "https://open.cnpja.com"
SERVICE_NAME = "CNPJá"
LEGAL_NATURE_LENGTH = 4
CNAE_LENGTH = 7


class CompanyLookup(ABC):
    @abstractmethod
    def get_company(self, tax_id: str) -> Company: ...


class CnpjaCompanyLookup(CompanyLookup):
    def __init__(self, client: httpx2.Client, base_url: str = CNPJA_URL) -> None:
        self._client = client
        self._base_url = base_url

    def get_company(self, tax_id: str) -> Company:
        if not TAX_ID_PATTERN.fullmatch(tax_id):
            raise InvalidCnpjError()
        url = f"{self._base_url}/office/{tax_id}"
        status_code, body = get_bytes(self._client, url, SERVICE_NAME)
        raise_for_status(status_code, tax_id)
        try:
            return company_from(tax_id, parse_json(body, SERVICE_NAME))
        except MALFORMED_BODY_ERRORS as error:
            raise ExternalServiceError(f"{SERVICE_NAME} sent an unexpected body") from error


def raise_for_status(status_code: int, tax_id: str) -> None:
    if status_code == HTTPStatus.BAD_REQUEST:
        raise InvalidCnpjError()
    if status_code == HTTPStatus.NOT_FOUND:
        raise CnpjNotFoundError(tax_id)
    if status_code != HTTPStatus.OK:
        raise ExternalServiceError(f"{SERVICE_NAME} answered HTTP {status_code}")


def company_from(tax_id: str, data: dict[str, Any]) -> Company:
    company = data["company"]
    return Company(
        tax_id=tax_id,
        legal_name=company["name"],
        trade_name=text_or_none(data["alias"]),
        registration_status=data["status"]["text"],
        legal_nature_code=code_from(company["nature"]["id"], LEGAL_NATURE_LENGTH),
        legal_nature_description=company["nature"]["text"],
        main_activity_code=code_from(data["mainActivity"]["id"], CNAE_LENGTH),
        main_activity_description=data["mainActivity"]["text"],
        address=address_from(data["address"]),
        raw_data=without_personal_data(data),
    )


def address_from(data: dict[str, Any]) -> Address:
    return Address(
        postal_code=text_or_none(data["zip"]),
        state=data["state"],
        city=data["city"],
        neighborhood=text_or_none(data["district"]),
        street=text_or_none(data["street"]),
        number=text_or_none(data["number"]),
        complement=text_or_none(data["details"]),
    )


def code_from(value: object, length: int) -> str:
    # CNPJá sends codes as numbers, which drops the leading zero of a CNAE.
    return str(value).zfill(length)


def text_or_none(value: object) -> object:
    # CNPJá sends "" for a missing text, while the schemas use None.
    if value == "":
        return None
    return value


def without_personal_data(data: dict[str, Any]) -> dict[str, Any]:
    # Partners and contacts are personal data the charity verdict never uses.
    facts = dict(data)
    facts.pop("phones", None)
    facts.pop("emails", None)
    facts["company"] = dict(data["company"])
    facts["company"].pop("members", None)
    return facts
