from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import httpx2

from src.connectors.exceptions import ExternalServiceError
from src.connectors.json_api import get_bytes, parse_json
from src.connectors.schemas import MALFORMED_BODY_ERRORS, Coordinates, Route
from src.domain.exceptions import RouteNotFoundError

OSRM_URL = "https://router.project-osrm.org"
SERVICE_NAME = "OSRM"
NO_ROUTE_CODES = ("NoRoute", "NoSegment")


class RoutePlanner(ABC):
    @abstractmethod
    def get_route(self, origin: Coordinates, destination: Coordinates) -> Route: ...


class OsrmRoutePlanner(RoutePlanner):
    def __init__(self, client: httpx2.Client, base_url: str = OSRM_URL) -> None:
        self._client = client
        self._base_url = base_url

    def get_route(self, origin: Coordinates, destination: Coordinates) -> Route:
        points = f"{longitude_latitude(origin)};{longitude_latitude(destination)}"
        # overview=false leaves the route geometry out of the answer.
        url = f"{self._base_url}/route/v1/driving/{points}?overview=false"
        status_code, body = get_bytes(self._client, url, SERVICE_NAME)
        raise_for_status(status_code)
        data = parse_json(body, SERVICE_NAME)
        raise_for_code(data.get("code"))
        try:
            return route_from(data)
        except MALFORMED_BODY_ERRORS as error:
            raise ExternalServiceError(f"{SERVICE_NAME} sent an unexpected body") from error


def raise_for_status(status_code: int) -> None:
    # OSRM puts the error code inside the JSON body of a 400 answer.
    if status_code not in (HTTPStatus.OK, HTTPStatus.BAD_REQUEST):
        raise ExternalServiceError(f"{SERVICE_NAME} answered HTTP {status_code}")


def raise_for_code(code: object) -> None:
    if code == "Ok":
        return
    if code in NO_ROUTE_CODES:
        raise RouteNotFoundError()
    raise ExternalServiceError(f"{SERVICE_NAME} answered with code {code!r}")


def route_from(data: dict[str, Any]) -> Route:
    route = data["routes"][0]
    return Route(distance_meters=route["distance"], duration_seconds=route["duration"])


def longitude_latitude(point: Coordinates) -> str:
    # OSRM takes longitude first, and fixed decimals avoid scientific notation.
    return f"{point.longitude:.6f},{point.latitude:.6f}"
