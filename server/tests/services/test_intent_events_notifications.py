import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import get_intent_event_publisher, get_notification_repository
from src.domain.enums import DonationIntentStatus, NotificationType, Role
from src.models.donation_intent import DonationIntent
from src.models.notification import Notification
from src.services.intent_events import IntentEvent
from tests.models.helpers import register_intent, save_donor, save_need


@pytest.fixture
def intent(db_session: Session) -> DonationIntent:
    return register_intent(db_session, save_need(db_session), save_donor(db_session))


def publish(
    db_session: Session,
    intent: DonationIntent,
    kind: NotificationType,
    actor: Role,
    new_status: DonationIntentStatus,
) -> list[Notification]:
    publisher = get_intent_event_publisher(get_notification_repository(db_session))
    publisher.notify(IntentEvent(kind, intent, actor, intent.status, new_status))
    # A rollback drops anything not committed, so only stored rows are read.
    db_session.rollback()
    return list(db_session.scalars(select(Notification)))


@pytest.mark.parametrize(
    ("kind", "new_status", "message"),
    [
        (
            NotificationType.INTENT_REGISTERED,
            DonationIntentStatus.REGISTERED,
            "Maria quer doar para a necessidade Ração.",
        ),
        (
            NotificationType.INTENT_CANCELLED,
            DonationIntentStatus.CANCELLED,
            "Maria cancelou a doação para a necessidade Ração.",
        ),
        (
            NotificationType.INTENT_DELIVERED,
            DonationIntentStatus.DELIVERED,
            "Maria marcou como entregue a doação para a necessidade Ração.",
        ),
    ],
)
def test_only_the_manager_is_notified_of_what_the_donor_does(
    db_session: Session,
    intent: DonationIntent,
    kind: NotificationType,
    new_status: DonationIntentStatus,
    message: str,
) -> None:
    [notification] = publish(db_session, intent, kind, Role.DONOR, new_status)

    assert notification.recipient_id == intent.need.institution.manager_id
    assert notification.type is kind
    assert notification.donation_intent_id == intent.id
    assert notification.message == message


@pytest.mark.parametrize(
    ("kind", "new_status", "label"),
    [
        (NotificationType.INTENT_STATUS_CHANGED, DonationIntentStatus.IN_CONTACT, "Em contato"),
        (
            NotificationType.INTENT_STATUS_CHANGED,
            DonationIntentStatus.DELIVERY_SCHEDULED,
            "Entrega agendada",
        ),
        (NotificationType.INTENT_STATUS_CHANGED, DonationIntentStatus.RECEIVED, "Recebida"),
        (NotificationType.INTENT_CANCELLED, DonationIntentStatus.CANCELLED, "Cancelada"),
    ],
)
def test_only_the_donor_is_notified_when_the_manager_changes_the_status(
    db_session: Session,
    intent: DonationIntent,
    kind: NotificationType,
    new_status: DonationIntentStatus,
    label: str,
) -> None:
    [notification] = publish(db_session, intent, kind, Role.MANAGER, new_status)

    assert notification.recipient_id == intent.donor_id
    assert notification.type is kind
    assert notification.donation_intent_id == intent.id
    assert notification.message == f"Sua doação para a necessidade Ração mudou para {label}."
