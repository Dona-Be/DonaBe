import pytest

from src.connectors.addresses import AddressLookup
from src.connectors.routing import RoutePlanner
from src.connectors.schemas import Address, Coordinates, Route
from src.domain.exceptions import CepNotFoundError, CepWithoutCoordinatesError, InvalidCepError
from src.services.locations import LocationService

PRACA_DA_SE = Coordinates(latitude=-23.5503898, longitude=-46.633081)
BRASILIA = Coordinates(latitude=-15.77972, longitude=-47.92972)
SE_ADDRESS = Address(postal_code="01001000", state="SP", city="São Paulo", coordinates=PRACA_DA_SE)
ROUTE = Route(distance_meters=1015234.5, duration_seconds=43210.7)


class FakeAddressLookup(AddressLookup):
    def __init__(self, answer: Address | Exception) -> None:
        self.answer = answer
        self.calls: list[str] = []

    def get_address(self, cep: str) -> Address:
        self.calls.append(cep)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


class FakeRoutePlanner(RoutePlanner):
    def __init__(self, route: Route) -> None:
        self.route = route
        self.calls: list[tuple[Coordinates, Coordinates]] = []

    def get_route(self, origin: Coordinates, destination: Coordinates) -> Route:
        self.calls.append((origin, destination))
        return self.route


def service_with(answer: Address | Exception) -> tuple[LocationService, FakeAddressLookup]:
    addresses = FakeAddressLookup(answer)
    return LocationService(addresses, FakeRoutePlanner(ROUTE)), addresses


def test_locate_normalizes_the_cep_and_returns_the_address() -> None:
    service, addresses = service_with(SE_ADDRESS)

    assert service.locate("01001-000") == SE_ADDRESS
    assert addresses.calls == ["01001000"]


def test_locate_rejects_an_address_without_coordinates() -> None:
    service, _ = service_with(Address(postal_code="69945000", state="AC", city="Acrelândia"))

    with pytest.raises(CepWithoutCoordinatesError, match="69945000"):
        service.locate("69945-000")


def test_locate_rejects_an_invalid_cep_without_calling_the_lookup() -> None:
    service, addresses = service_with(SE_ADDRESS)

    with pytest.raises(InvalidCepError):
        service.locate("0100100")

    assert addresses.calls == []


def test_locate_propagates_a_cep_that_was_not_found() -> None:
    service, _ = service_with(CepNotFoundError("01001000"))

    with pytest.raises(CepNotFoundError):
        service.locate("01001000")


def test_route_between_asks_the_route_planner() -> None:
    routes = FakeRoutePlanner(ROUTE)
    service = LocationService(FakeAddressLookup(SE_ADDRESS), routes)

    assert service.route_between(PRACA_DA_SE, BRASILIA) == ROUTE
    assert routes.calls == [(PRACA_DA_SE, BRASILIA)]
