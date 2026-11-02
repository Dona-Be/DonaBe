from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import httpx2

from src.connectors.exceptions import ExternalServiceError
from src.connectors.json_api import get_bytes, parse_json
from src.connectors.schemas import MALFORMED_BODY_ERRORS, Address, Coordinates
from src.domain.cep import CEP_DIGITS
from src.domain.exceptions import CepNotFoundError, InvalidCepError

BRASILAPI_URL = "https://brasilapi.com.br/api"
SERVICE_NAME = "BrasilAPI"


class AddressLookup(ABC):
    @abstractmethod
    def get_address(self, cep: str) -> Address: ...


class BrasilApiAddressLookup(AddressLookup):
    def __init__(self, client: httpx2.Client, base_url: str = BRASILAPI_URL) -> None:
        self._client = client
        self._base_url = base_url

    def get_address(self, cep: str) -> Address:
        if not CEP_DIGITS.fullmatch(cep):
            raise InvalidCepError()
        url = f"{self._base_url}/cep/v2/{cep}"
        status_code, body = get_bytes(self._client, url, SERVICE_NAME)
        raise_for_status(status_code, cep)
        try:
            return address_from(parse_json(body, SERVICE_NAME))
        except MALFORMED_BODY_ERRORS as error:
            raise ExternalServiceError(f"{SERVICE_NAME} sent an unexpected body") from error


def raise_for_status(status_code: int, cep: str) -> None:
    if status_code == HTTPStatus.BAD_REQUEST:
        raise InvalidCepError()
    if status_code == HTTPStatus.NOT_FOUND:
        raise CepNotFoundError(cep)
    if status_code != HTTPStatus.OK:
        raise ExternalServiceError(f"{SERVICE_NAME} answered HTTP {status_code}")


def address_from(data: dict[str, Any]) -> Address:
    return Address(
        postal_code=data["cep"],
        state=data["state"],
        city=data["city"],
        neighborhood=data["neighborhood"],
        street=data["street"],
        coordinates=coordinates_from(data),
    )


def coordinates_from(data: dict[str, Any]) -> Coordinates | None:
    location = data.get("location")
    if not location:
        return None
    raw = location.get("coordinates")
    if not raw:
        return None
    latitude = raw.get("latitude")
    longitude = raw.get("longitude")
    if latitude in (None, "") or longitude in (None, ""):
        return None
    return Coordinates(latitude=latitude, longitude=longitude)
