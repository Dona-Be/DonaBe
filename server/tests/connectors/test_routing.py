import httpx2
import pytest
from pydantic import ValidationError

from src.connectors.exceptions import ExternalServiceError, RateLimitedError
from src.connectors.json_api import DEFAULT_TIMEOUT
from src.connectors.routing import OsrmRoutePlanner
from src.connectors.schemas import Coordinates, Route
from src.domain.exceptions import RouteNotFoundError
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import AV_DO_ESTADO, PRACA_DA_SE, ROUTE_OK

# Python reads 1e999 as infinity.
INFINITE_DISTANCE = b'{"code": "Ok", "routes": [{"distance": 1e999, "duration": 1}]}'
INFINITE_DURATION = b'{"code": "Ok", "routes": [{"distance": 1, "duration": 1e999}]}'
BOOLEAN_DISTANCE = {"code": "Ok", "routes": [{"distance": True, "duration": 1}]}


def test_get_route_calls_the_default_url_and_returns_the_route(
    fake_api: FakeApi, route_planner: OsrmRoutePlanner
) -> None:
    fake_api.response = httpx2.Response(200, json=ROUTE_OK)

    route = route_planner.get_route(PRACA_DA_SE, AV_DO_ESTADO)

    assert route == Route(distance_meters=3570.3, duration_seconds=395.2)
    assert str(fake_api.requests[0].url) == (
        "https://router.project-osrm.org/route/v1/driving/"
        "-46.633309,-23.550520;-46.625290,-23.533773?overview=false"
    )
    assert fake_api.requests[0].extensions["timeout"] == httpx2.Timeout(DEFAULT_TIMEOUT).as_dict()


def test_get_route_calls_the_configured_url(fake_api: FakeApi) -> None:
    fake_api.response = httpx2.Response(200, json=ROUTE_OK)
    planner = OsrmRoutePlanner(fake_api.client(), base_url="https://osrm.interno")

    planner.get_route(PRACA_DA_SE, AV_DO_ESTADO)

    assert str(fake_api.requests[0].url).startswith("https://osrm.interno/route/v1/driving/")


def test_get_route_writes_small_coordinates_without_an_exponent(
    fake_api: FakeApi, route_planner: OsrmRoutePlanner
) -> None:
    fake_api.response = httpx2.Response(200, json=ROUTE_OK)

    route_planner.get_route(Coordinates(latitude=0.00001, longitude=-50.0), AV_DO_ESTADO)

    assert fake_api.requests[0].url.path.startswith("/route/v1/driving/-50.000000,0.000010;")


@pytest.mark.parametrize("code", ["NoRoute", "NoSegment"])
def test_get_route_reports_when_there_is_no_route(
    code: str, fake_api: FakeApi, route_planner: OsrmRoutePlanner
) -> None:
    fake_api.response = httpx2.Response(400, json={"code": code, "message": "no route"})

    with pytest.raises(RouteNotFoundError):
        route_planner.get_route(PRACA_DA_SE, AV_DO_ESTADO)


def test_get_route_reports_a_rate_limit(fake_api: FakeApi, route_planner: OsrmRoutePlanner) -> None:
    fake_api.response = httpx2.Response(429, text="Too Many Requests")

    with pytest.raises(RateLimitedError):
        route_planner.get_route(PRACA_DA_SE, AV_DO_ESTADO)


@pytest.mark.parametrize(
    ("response", "log_message"),
    [
        (httpx2.Response(503, text="<html>Service Unavailable</html>"), "OSRM answered HTTP 503"),
        (httpx2.Response(203, json=ROUTE_OK), "OSRM answered HTTP 203"),
        (
            httpx2.Response(200, json={**ROUTE_OK, "code": "InvalidValue"}),
            "OSRM answered with code 'InvalidValue'",
        ),
        (httpx2.Response(400, json={"message": "no code"}), "OSRM answered with code None"),
        (httpx2.Response(200, text="not json"), "OSRM sent invalid JSON"),
        (httpx2.Response(200, json=["Ok"]), "OSRM sent a JSON body that is not an object"),
        (httpx2.Response(200, json={"code": "Ok", "routes": []}), "OSRM sent an unexpected body"),
        (httpx2.Response(200, json={"code": "Ok"}), "OSRM sent an unexpected body"),
        (httpx2.Response(200, json={"code": "Ok", "routes": None}), "OSRM sent an unexpected body"),
        (
            httpx2.Response(200, json={"code": "Ok", "routes": [{"distance": -1, "duration": 1}]}),
            "OSRM sent an unexpected body",
        ),
        (
            httpx2.Response(200, json={"code": "Ok", "routes": [{"distance": 1, "duration": -1}]}),
            "OSRM sent an unexpected body",
        ),
        (
            httpx2.Response(200, json=BOOLEAN_DISTANCE),
            "OSRM sent an unexpected body",
        ),
        (httpx2.Response(200, content=INFINITE_DISTANCE), "OSRM sent an unexpected body"),
        (httpx2.Response(200, content=INFINITE_DURATION), "OSRM sent an unexpected body"),
        (httpx2.ConnectError("no network"), "OSRM request failed"),
    ],
    ids=[
        "503 without json",
        "203 with route",
        "200 with an error code",
        "400 without code",
        "not json",
        "list",
        "no routes",
        "no routes field",
        "null routes",
        "negative distance",
        "negative duration",
        "boolean distance",
        "infinite distance",
        "infinite duration",
        "network",
    ],
)
def test_get_route_maps_failures(
    response: httpx2.Response | Exception,
    log_message: str,
    fake_api: FakeApi,
    route_planner: OsrmRoutePlanner,
) -> None:
    fake_api.response = response

    with pytest.raises(ExternalServiceError) as caught:
        route_planner.get_route(PRACA_DA_SE, AV_DO_ESTADO)

    assert caught.value.log_message == log_message


def test_get_route_keeps_the_validation_error_as_the_cause(
    fake_api: FakeApi, route_planner: OsrmRoutePlanner
) -> None:
    body = {"code": "Ok", "routes": [{"distance": None, "duration": 1}]}
    fake_api.response = httpx2.Response(200, json=body)

    with pytest.raises(ExternalServiceError) as caught:
        route_planner.get_route(PRACA_DA_SE, AV_DO_ESTADO)

    assert isinstance(caught.value.__cause__, ValidationError)
