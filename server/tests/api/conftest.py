from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.dependencies import get_address_lookup, get_company_lookup, get_http_client
from src.api.rate_limits import CEP_LOOKUPS_PER_ACCOUNT, CNPJ_LOOKUPS_PER_ACCOUNT
from src.connectors.addresses import address_from
from src.connectors.companies import company_from
from src.domain.enums import Cause, NotificationType
from src.models.donation_intent import DonationIntent
from src.models.notification import Notification
from src.models.user import Donor, Manager, User
from tests.api.helpers import (
    GOOGLE_CALLBACK,
    NOTIFICATION_MESSAGE,
    Notify,
    create_donor,
    sign_up,
)
from tests.connectors.fakes import FakeApi
from tests.connectors.samples import AACD, AACD_TAX_ID, PAULISTA
from tests.fakes import USER_EMAIL, FakeAddressLookup, FakeCompanyLookup
from tests.models.helpers import point_at, profile, register_intent, save_need


@pytest.fixture(autouse=True)
def reset_rate_limits() -> None:
    CEP_LOOKUPS_PER_ACCOUNT.reset()
    CNPJ_LOOKUPS_PER_ACCOUNT.reset()


@pytest.fixture
def donor(db_session: Session) -> Donor:
    return create_donor(db_session)


@pytest.fixture
def located_donor_client(client: TestClient, db_session: Session) -> TestClient:
    donor = Donor.from_profile(
        profile(USER_EMAIL),
        postal_code="01310200",
        location=point_at(0),
        preferred_causes=[Cause.ANIMALS],
    )
    db_session.add(donor)
    db_session.commit()
    # The donor is already registered, so the Google login starts the session.
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    return client


@pytest.fixture
def brasilapi(client: TestClient, fake_api: FakeApi) -> FakeApi:
    fake_api.response = httpx2.Response(200, json=PAULISTA)
    client.app.dependency_overrides[get_http_client] = fake_api.client
    return fake_api


@pytest.fixture
def companies(client: TestClient) -> FakeCompanyLookup:
    fake = FakeCompanyLookup(company_from(AACD_TAX_ID, AACD))
    client.app.dependency_overrides[get_company_lookup] = lambda: fake
    return fake


@pytest.fixture
def addresses(client: TestClient) -> FakeAddressLookup:
    fake = FakeAddressLookup(address_from(PAULISTA))
    client.app.dependency_overrides[get_address_lookup] = lambda: fake
    return fake


@pytest.fixture
def manager_client(
    client: TestClient, companies: FakeCompanyLookup, addresses: FakeAddressLookup
) -> TestClient:
    sign_up(client, "manager")
    return client


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
