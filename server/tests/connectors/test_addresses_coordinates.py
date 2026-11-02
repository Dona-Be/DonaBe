import json

import httpx2
import pytest

from src.connectors.exceptions import ExternalServiceError
from tests.connectors.helpers import address_lookup_with
from tests.connectors.samples import PAULISTA


@pytest.mark.parametrize(
    "location",
    [
        None,
        {"type": "Point", "coordinates": None},
        {"type": "Point", "coordinates": {"longitude": None, "latitude": None}},
        {"type": "Point", "coordinates": {"longitude": "-46.6"}},
        {"type": "Point", "coordinates": {"latitude": "-23.5"}},
        {"type": "Point", "coordinates": {"latitude": "", "longitude": "-46.6"}},
        {"type": "Point", "coordinates": {"latitude": "-23.5", "longitude": ""}},
    ],
    ids=[
        "no location",
        "no coordinates",
        "null coordinates",
        "no latitude",
        "no longitude",
        "empty latitude",
        "empty longitude",
    ],
)
def test_get_address_returns_no_coordinates_when_they_are_missing(location: object) -> None:
    body = {**PAULISTA, "location": location}
    lookup, _ = address_lookup_with(httpx2.Response(200, json=body))

    assert lookup.get_address("01310200").coordinates is None


@pytest.mark.parametrize(
    "coordinates",
    [
        {"latitude": "abc", "longitude": "-46.6"},
        {"latitude": "-95", "longitude": "-46.6"},
        {"latitude": "95", "longitude": "-46.6"},
        {"latitude": "-23.5", "longitude": "-200"},
        {"latitude": "-23.5", "longitude": "200"},
        {"latitude": True, "longitude": "-46.6"},
        [-46.63611, -23.5475],
    ],
    ids=[
        "not a number",
        "latitude below the range",
        "latitude above the range",
        "longitude below the range",
        "longitude above the range",
        "boolean",
        "geojson list",
    ],
)
def test_get_address_rejects_invalid_coordinates(coordinates: object) -> None:
    body = {**PAULISTA, "location": {"type": "Point", "coordinates": coordinates}}
    lookup, _ = address_lookup_with(httpx2.Response(200, json=body))

    with pytest.raises(ExternalServiceError):
        lookup.get_address("01310200")


def test_get_address_rejects_a_nan_coordinate() -> None:
    coordinates = {"latitude": float("nan"), "longitude": "-46.6"}
    body = json.dumps({**PAULISTA, "location": {"coordinates": coordinates}}).encode()
    lookup, _ = address_lookup_with(httpx2.Response(200, content=body))

    with pytest.raises(ExternalServiceError):
        lookup.get_address("01310200")
