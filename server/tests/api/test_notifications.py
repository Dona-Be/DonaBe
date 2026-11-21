from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.user import Donor, Manager
from tests.api.helpers import GOOGLE_CALLBACK, NOTIFICATION_MESSAGE, Notify

NOTIFICATIONS = "/api/notifications"
READ_AT = datetime(2026, 2, 1, tzinfo=UTC)


@pytest.fixture
def donor_client(client: TestClient, donor: Donor) -> TestClient:
    # The donor is already registered, so the Google login starts the session.
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    return client


def listed_ids(client: TestClient, **params: Any) -> list[int]:
    return [listed["id"] for listed in client.get(NOTIFICATIONS, params=params).json()]


def test_lists_only_your_notifications_from_newest_to_oldest(
    donor_client: TestClient, notify: Notify, manager: Manager
) -> None:
    middle = notify(created_at=datetime(2026, 1, 2, tzinfo=UTC))
    oldest = notify(created_at=datetime(2026, 1, 1, tzinfo=UTC))
    newest = notify(created_at=datetime(2026, 1, 3, tzinfo=UTC))
    notify(manager)

    response = donor_client.get(NOTIFICATIONS)

    assert response.status_code == 200
    assert [listed["id"] for listed in response.json()] == [newest.id, middle.id, oldest.id]
    first = response.json()[0]
    assert datetime.fromisoformat(first.pop("created_at")) == newest.created_at
    assert first == {
        "id": newest.id,
        "type": "intent_status_changed",
        "message": NOTIFICATION_MESSAGE,
        "donation_intent_id": newest.donation_intent_id,
        "read_at": None,
    }


def test_each_page_has_20_notifications(donor_client: TestClient, notify: Notify) -> None:
    for _ in range(21):
        notify(created_at=datetime(2026, 1, 1, tzinfo=UTC))

    assert listed_ids(donor_client) == list(range(21, 1, -1))
    assert listed_ids(donor_client, page=2) == [1]


@pytest.mark.parametrize(
    ("method", "path"), [("GET", "?page=0"), ("GET", f"?page={2**31}"), ("POST", f"/{2**31}/read")]
)
def test_rejects_numbers_out_of_range(donor_client: TestClient, method: str, path: str) -> None:
    response = donor_client.request(method, NOTIFICATIONS + path)

    assert response.status_code == 422


def test_unread_lists_only_what_was_not_read_yet(donor_client: TestClient, notify: Notify) -> None:
    read = notify(read_at=READ_AT)
    unread = notify()

    assert listed_ids(donor_client, unread="true") == [unread.id]
    assert listed_ids(donor_client, unread="false") == [unread.id, read.id]


def test_counts_only_your_unread_notifications(
    donor_client: TestClient, notify: Notify, manager: Manager
) -> None:
    notify(read_at=READ_AT)
    notify()
    notify()
    notify(manager)

    assert donor_client.get(f"{NOTIFICATIONS}/unread-count").json() == {"count": 2}


def test_marks_one_notification_as_read(donor_client: TestClient, notify: Notify) -> None:
    oldest = notify()
    notify()

    response = donor_client.post(f"{NOTIFICATIONS}/{oldest.id}/read")

    assert response.status_code == 204
    still_unread, read = donor_client.get(NOTIFICATIONS).json()
    assert still_unread["read_at"] is None
    assert datetime.fromisoformat(read["read_at"]) > READ_AT


def test_reading_again_keeps_the_first_read_date(donor_client: TestClient, notify: Notify) -> None:
    read = notify(read_at=READ_AT)

    response = donor_client.post(f"{NOTIFICATIONS}/{read.id}/read")

    assert response.status_code == 204
    [listed] = donor_client.get(NOTIFICATIONS).json()
    assert datetime.fromisoformat(listed["read_at"]) == READ_AT


@pytest.mark.parametrize("notification_id", [1, 2], ids=["someone else's", "missing"])
def test_only_your_own_notification_can_be_marked_as_read(
    donor_client: TestClient,
    notify: Notify,
    manager: Manager,
    db_session: Session,
    notification_id: int,
) -> None:
    theirs = notify(manager)

    response = donor_client.post(f"{NOTIFICATIONS}/{notification_id}/read")

    assert response.status_code == 404
    assert response.json() == {"detail": "Notificação não encontrada."}
    db_session.refresh(theirs)
    assert theirs.read_at is None


def test_read_all_marks_only_your_unread_notifications(
    donor_client: TestClient, notify: Notify, manager: Manager, db_session: Session
) -> None:
    notify(read_at=READ_AT)
    notify()
    theirs = notify(manager)

    response = donor_client.post(f"{NOTIFICATIONS}/read-all")

    assert response.status_code == 204
    newest, oldest = donor_client.get(NOTIFICATIONS).json()
    assert datetime.fromisoformat(newest["read_at"]) > READ_AT
    assert datetime.fromisoformat(oldest["read_at"]) == READ_AT
    db_session.refresh(theirs)
    assert theirs.read_at is None


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", ""), ("GET", "/unread-count"), ("POST", "/read-all"), ("POST", "/1/read")],
)
def test_notifications_require_a_logged_in_user(client: TestClient, method: str, path: str) -> None:
    response = client.request(method, NOTIFICATIONS + path)

    assert response.status_code == 401
    assert response.json() == {"detail": "Você precisa entrar para continuar."}
