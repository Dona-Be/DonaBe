import httpx2
import pytest
from pydantic import ValidationError

from src.connectors.addresses import BrasilApiAddressLookup
from src.connectors.exceptions import ExternalServiceError, RateLimitedError
from src.connectors.json_api import DEFAULT_TIMEOUT
from src.connectors.schemas import Address, Coordinates
from src.domain.exceptions import CepNotFoundError, InvalidCepError
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import ACRELANDIA, CEP_INVALID, CEP_NOT_FOUND, PAULISTA
from tests.helpers import fullwidth

PAULISTA_ADDRESS = Address(
    postal_code="01310200",
    state="SP",
    city="São Paulo",
    neighborhood="Bela Vista",
    street="Avenida Paulista",
    coordinates=Coordinates(latitude=-23.5475, longitude=-46.63611),
)


def test_get_address_calls_the_default_url_and_returns_the_address(
    fake_api: FakeApi, address_lookup: BrasilApiAddressLookup
) -> None:
    fake_api.response = httpx2.Response(200, json=PAULISTA)

    address = address_lookup.get_address("01310200")

    assert address == PAULISTA_ADDRESS
    assert str(fake_api.requests[0].url) == "https://brasilapi.com.br/api/cep/v2/01310200"
    assert fake_api.requests[0].extensions["timeout"] == httpx2.Timeout(DEFAULT_TIMEOUT).as_dict()


def test_get_address_calls_the_configured_url(fake_api: FakeApi) -> None:
    fake_api.response = httpx2.Response(200, json=PAULISTA)
    lookup = BrasilApiAddressLookup(fake_api.client(), base_url="https://cep.interno")

    lookup.get_address("01310200")

    assert str(fake_api.requests[0].url) == "https://cep.interno/cep/v2/01310200"


def test_get_address_accepts_a_cep_without_street(
    fake_api: FakeApi, address_lookup: BrasilApiAddressLookup
) -> None:
    fake_api.response = httpx2.Response(200, json=ACRELANDIA)

    address = address_lookup.get_address("69945000")

    assert (address.street, address.neighborhood) == (None, None)
    assert address.coordinates == Coordinates(latitude=-10.07387, longitude=-67.055)


@pytest.mark.parametrize(
    "cep",
    ["", "01310-200", " 01310200 ", "1310200", "0131020a", "013102000", fullwidth("01310200")],
    ids=["empty", "dash", "spaces", "seven digits", "letter", "nine digits", "non ascii digits"],
)
def test_get_address_only_accepts_the_eight_digits_the_service_normalized(
    cep: str, fake_api: FakeApi, address_lookup: BrasilApiAddressLookup
) -> None:
    with pytest.raises(InvalidCepError):
        address_lookup.get_address(cep)

    assert fake_api.requests == []


@pytest.mark.parametrize(
    ("response", "error"),
    [
        (httpx2.Response(400, json=CEP_INVALID), InvalidCepError),
        (httpx2.Response(404, json=CEP_NOT_FOUND), CepNotFoundError),
        (httpx2.Response(429, text="Too Many Requests"), RateLimitedError),
        (httpx2.Response(500, text="Internal Server Error"), ExternalServiceError),
        (httpx2.Response(203, json=PAULISTA), ExternalServiceError),
        (httpx2.Response(200, json=[]), ExternalServiceError),
        (httpx2.Response(200, json={**PAULISTA, "city": None}), ExternalServiceError),
        (httpx2.Response(200, json={**PAULISTA, "state": "sp"}), ExternalServiceError),
        (
            httpx2.Response(200, json={**PAULISTA, "cep": fullwidth("01310200")}),
            ExternalServiceError,
        ),
        (httpx2.Response(200, json={**PAULISTA, "cep": "013102000"}), ExternalServiceError),
        (httpx2.ConnectError("no network"), ExternalServiceError),
    ],
    ids=[
        "400",
        "404",
        "429",
        "500 without json",
        "203 with address",
        "list",
        "without city",
        "lower case state",
        "non ascii cep",
        "nine digit cep",
        "network",
    ],
)
def test_get_address_maps_failures(
    response: httpx2.Response | Exception,
    error: type[Exception],
    fake_api: FakeApi,
    address_lookup: BrasilApiAddressLookup,
) -> None:
    fake_api.response = response

    with pytest.raises(error):
        address_lookup.get_address("01310200")


def test_get_address_names_the_cep_that_was_not_found(
    fake_api: FakeApi, address_lookup: BrasilApiAddressLookup
) -> None:
    fake_api.response = httpx2.Response(404, json=CEP_NOT_FOUND)

    with pytest.raises(CepNotFoundError, match="01310200"):
        address_lookup.get_address("01310200")


def test_get_address_keeps_the_validation_error_as_the_cause(
    fake_api: FakeApi, address_lookup: BrasilApiAddressLookup
) -> None:
    fake_api.response = httpx2.Response(200, json={**PAULISTA, "state": None})

    with pytest.raises(ExternalServiceError) as caught:
        address_lookup.get_address("01310200")

    assert caught.value.log_message == "BrasilAPI sent an unexpected body"
    assert isinstance(caught.value.__cause__, ValidationError)
