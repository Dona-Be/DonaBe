import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.enums import NotificationType
from src.models.donation_intent import DonationIntent
from src.models.need import Need
from src.models.notification import NOTIFICATIONS_BY_RECIPIENT_INDEX, Notification
from src.models.user import Donor
from tests.models.helpers import register_intent

MESSAGE = "Maria quer doar para a necessidade Ração."


@pytest.fixture
def intent(db_session: Session, need: Need, donor: Donor) -> DonationIntent:
    return register_intent(db_session, need, donor)


def notification_fields(intent: DonationIntent) -> dict[str, object]:
    return {
        "recipient": intent.need.institution.manager,
        "type": NotificationType.INTENT_REGISTERED,
        "donation_intent": intent,
        "message": MESSAGE,
    }


def test_notifications_are_indexed_by_recipient_then_read_at() -> None:
    indexes = {index.name: index for index in Notification.__table__.indexes}

    recipient_index = indexes[NOTIFICATIONS_BY_RECIPIENT_INDEX]

    assert [column.name for column in recipient_index.columns] == ["recipient_id", "read_at"]


def test_a_new_notification_is_unread_and_dated(
    db_session: Session, intent: DonationIntent
) -> None:
    notification = Notification(**notification_fields(intent))

    db_session.add(notification)
    db_session.commit()

    assert notification.read_at is None
    assert notification.created_at is not None


@pytest.mark.parametrize(
    ("field", "column"),
    [
        ("recipient", "recipient_id"),
        ("type", "type"),
        ("donation_intent", "donation_intent_id"),
        ("message", "message"),
    ],
)
def test_a_notification_requires_its_fields(
    db_session: Session, intent: DonationIntent, field: str, column: str
) -> None:
    fields = notification_fields(intent)
    del fields[field]
    db_session.add(Notification(**fields))

    with pytest.raises(IntegrityError, match=f'column "{column}"'):
        db_session.commit()
