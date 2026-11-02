from src.connectors.addresses import AddressLookup
from src.connectors.routing import RoutePlanner
from src.connectors.schemas import Address, Coordinates, Route
from src.domain.cep import normalize_cep
from src.domain.exceptions import CepWithoutCoordinatesError


class LocationService:
    def __init__(self, addresses: AddressLookup, routes: RoutePlanner) -> None:
        self._addresses = addresses
        self._routes = routes

    def locate(self, cep: str) -> Address:
        digits = normalize_cep(cep)
        address = self._addresses.get_address(digits)
        if address.coordinates is None:
            raise CepWithoutCoordinatesError(digits)
        return address

    def route_between(self, origin: Coordinates, destination: Coordinates) -> Route:
        return self._routes.get_route(origin, destination)
