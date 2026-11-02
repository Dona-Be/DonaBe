import time

import pytest

from src.connectors.addresses import BrasilApiAddressLookup
from src.connectors.companies import CnpjaCompanyLookup
from src.connectors.routing import OsrmRoutePlanner
from tests.connectors.fakes import FakeApi, FakeClock


@pytest.fixture
def address_lookup(fake_api: FakeApi) -> BrasilApiAddressLookup:
    return BrasilApiAddressLookup(fake_api.client())


@pytest.fixture
def company_lookup(fake_api: FakeApi) -> CnpjaCompanyLookup:
    return CnpjaCompanyLookup(fake_api.client())


@pytest.fixture
def route_planner(fake_api: FakeApi) -> OsrmRoutePlanner:
    return OsrmRoutePlanner(fake_api.client())


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    # Each clock reading adds one second, so a deadline passes within a test.
    clock = FakeClock()
    monkeypatch.setattr(time, "monotonic", clock.monotonic)
    return clock
