import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.dependencies import get_http_client
from src.api.rate_limits import CEP_LOOKUPS_PER_ACCOUNT
from src.models.user import Donor
from tests.api.helpers import create_donor
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import PAULISTA


@pytest.fixture(autouse=True)
def reset_rate_limits() -> None:
    CEP_LOOKUPS_PER_ACCOUNT.reset()


@pytest.fixture
def donor(db_session: Session) -> Donor:
    return create_donor(db_session)


@pytest.fixture
def brasilapi(client: TestClient, fake_api: FakeApi) -> FakeApi:
    fake_api.response = httpx2.Response(200, json=PAULISTA)
    client.app.dependency_overrides[get_http_client] = fake_api.client
    return fake_api
