from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.dependencies import get_http_client
from src.api.rate_limits import CEP_LOOKUPS_PER_ACCOUNT
from src.domain.enums import NotificationType
from src.models.donation_intent import DonationIntent
from src.models.notification import Notification
from src.models.user import Donor, Manager, User
from tests.api.helpers import NOTIFICATION_MESSAGE, Notify, create_donor
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import PAULISTA
from tests.models.helpers import register_intent, save_need


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


@pytest.fixture
def intent(db_session: Session, donor: Donor) -> DonationIntent:
    return register_intent(db_session, save_need(db_session), donor)


@pytest.fixture
def manager(intent: DonationIntent) -> Manager:
    return intent.need.institution.manager


@pytest.fixture
def notify(db_session: Session, intent: DonationIntent) -> Notify:
    def save(recipient: User = intent.donor, **fields: Any) -> Notification:
        notification = Notification(
            recipient=recipient,
            type=NotificationType.INTENT_STATUS_CHANGED,
            donation_intent=intent,
            message=NOTIFICATION_MESSAGE,
            **fields,
        )
        db_session.add(notification)
        db_session.commit()
        return notification

    return save
