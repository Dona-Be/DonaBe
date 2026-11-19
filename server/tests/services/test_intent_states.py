from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from src.domain.enums import DonationIntentStatus, Role
from src.domain.exceptions import InvalidTransitionError
from src.models.donation_intent import DonationIntent
from src.services.intent_states import IntentState, state_of

DATE_FIELDS = ("contacted_at", "scheduled_for", "delivered_at", "received_at", "cancelled_at")


def days_from_now(days: int) -> datetime:
    return datetime.now(UTC) + timedelta(days=days)


TRANSITIONS: dict[str, Callable[[IntentState, Role], None]] = {
    "start_contact": lambda state, actor: state.start_contact(actor),
    "schedule_delivery": lambda state, actor: state.schedule_delivery(actor, days_from_now(1)),
    "mark_delivered": lambda state, actor: state.mark_delivered(actor),
    "confirm_receipt": lambda state, actor: state.confirm_receipt(actor),
    "cancel": lambda state, actor: state.cancel(actor),
}
NEXT_STATUS = {
    "start_contact": DonationIntentStatus.IN_CONTACT,
    "schedule_delivery": DonationIntentStatus.DELIVERY_SCHEDULED,
    "mark_delivered": DonationIntentStatus.DELIVERED,
    "confirm_receipt": DonationIntentStatus.RECEIVED,
    "cancel": DonationIntentStatus.CANCELLED,
}
ALLOWED = [
    (DonationIntentStatus.REGISTERED, "start_contact", Role.MANAGER),
    (DonationIntentStatus.IN_CONTACT, "schedule_delivery", Role.MANAGER),
    (DonationIntentStatus.DELIVERY_SCHEDULED, "mark_delivered", Role.DONOR),
    (DonationIntentStatus.DELIVERED, "confirm_receipt", Role.MANAGER),
    (DonationIntentStatus.REGISTERED, "cancel", Role.DONOR),
    (DonationIntentStatus.REGISTERED, "cancel", Role.MANAGER),
    (DonationIntentStatus.IN_CONTACT, "cancel", Role.DONOR),
    (DonationIntentStatus.IN_CONTACT, "cancel", Role.MANAGER),
    (DonationIntentStatus.DELIVERY_SCHEDULED, "cancel", Role.DONOR),
    (DonationIntentStatus.DELIVERY_SCHEDULED, "cancel", Role.MANAGER),
]
REFUSED = [
    (status, transition, actor)
    for status in DonationIntentStatus
    for transition in TRANSITIONS
    for actor in Role
    if (status, transition, actor) not in ALLOWED
]


def filled_dates(intent: DonationIntent) -> set[str]:
    return {field for field in DATE_FIELDS if getattr(intent, field) is not None}


@pytest.mark.parametrize(("status", "transition", "actor"), ALLOWED)
def test_an_allowed_transition_moves_the_intent_to_the_next_status(
    status: DonationIntentStatus, transition: str, actor: Role
) -> None:
    intent = DonationIntent(status=status)

    TRANSITIONS[transition](state_of(intent), actor)

    assert intent.status is NEXT_STATUS[transition]


@pytest.mark.parametrize(("status", "transition", "actor"), REFUSED)
def test_any_other_transition_or_role_is_refused_without_changes(
    status: DonationIntentStatus, transition: str, actor: Role
) -> None:
    intent = DonationIntent(status=status)
    state = state_of(intent)

    with pytest.raises(InvalidTransitionError):
        TRANSITIONS[transition](state, actor)

    assert intent.status is status
    assert filled_dates(intent) == set()


@pytest.mark.parametrize(
    ("status", "transition", "actor", "field"),
    [
        (DonationIntentStatus.REGISTERED, "start_contact", Role.MANAGER, "contacted_at"),
        (DonationIntentStatus.DELIVERY_SCHEDULED, "mark_delivered", Role.DONOR, "delivered_at"),
        (DonationIntentStatus.DELIVERED, "confirm_receipt", Role.MANAGER, "received_at"),
        (DonationIntentStatus.IN_CONTACT, "cancel", Role.DONOR, "cancelled_at"),
    ],
)
def test_a_transition_fills_its_date_with_the_current_time(
    status: DonationIntentStatus, transition: str, actor: Role, field: str
) -> None:
    intent = DonationIntent(status=status)
    before = datetime.now(UTC)

    TRANSITIONS[transition](state_of(intent), actor)

    assert filled_dates(intent) == {field}
    assert before <= getattr(intent, field) <= datetime.now(UTC)


def test_scheduling_a_delivery_keeps_the_chosen_date() -> None:
    intent = DonationIntent(status=DonationIntentStatus.IN_CONTACT)
    date = days_from_now(3)

    state_of(intent).schedule_delivery(Role.MANAGER, date)

    assert filled_dates(intent) == {"scheduled_for"}
    assert intent.scheduled_for == date


def test_a_delivery_cannot_be_scheduled_in_the_past() -> None:
    intent = DonationIntent(status=DonationIntentStatus.IN_CONTACT)
    state = state_of(intent)
    yesterday = days_from_now(-1)

    with pytest.raises(InvalidTransitionError):
        state.schedule_delivery(Role.MANAGER, yesterday)

    assert intent.status is DonationIntentStatus.IN_CONTACT
    assert filled_dates(intent) == set()


@pytest.mark.parametrize("actor", list(Role))
def test_cancelling_records_who_cancelled(actor: Role) -> None:
    intent = DonationIntent(status=DonationIntentStatus.DELIVERY_SCHEDULED)

    state_of(intent).cancel(actor)

    assert intent.cancelled_by is actor
