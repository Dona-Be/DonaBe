from abc import ABC
from datetime import UTC, datetime
from typing import ClassVar

from src.domain.enums import DonationIntentStatus, Role
from src.domain.exceptions import InvalidTransitionError
from src.models.donation_intent import DonationIntent


def require_role(actor: Role, role: Role) -> None:
    if actor != role:
        raise InvalidTransitionError()


class IntentState(ABC):
    status: ClassVar[DonationIntentStatus]

    def __init__(self, intent: DonationIntent) -> None:
        self._intent = intent

    def start_contact(self, actor: Role) -> None:
        raise InvalidTransitionError()

    def schedule_delivery(self, actor: Role, date: datetime) -> None:
        raise InvalidTransitionError()

    def mark_delivered(self, actor: Role) -> None:
        raise InvalidTransitionError()

    def confirm_receipt(self, actor: Role) -> None:
        raise InvalidTransitionError()

    def cancel(self, actor: Role) -> None:
        raise InvalidTransitionError()

    def _move_to(self, state: type["IntentState"]) -> None:
        self._intent.status = state.status


class CancellableState(IntentState):
    def cancel(self, actor: Role) -> None:
        self._move_to(Cancelled)
        self._intent.cancelled_at = datetime.now(UTC)
        self._intent.cancelled_by = actor


class Registered(CancellableState):
    status = DonationIntentStatus.REGISTERED

    def start_contact(self, actor: Role) -> None:
        require_role(actor, Role.MANAGER)
        self._move_to(InContact)
        self._intent.contacted_at = datetime.now(UTC)


class InContact(CancellableState):
    status = DonationIntentStatus.IN_CONTACT

    def schedule_delivery(self, actor: Role, date: datetime) -> None:
        require_role(actor, Role.MANAGER)
        if date <= datetime.now(UTC):
            raise InvalidTransitionError()
        self._move_to(DeliveryScheduled)
        self._intent.scheduled_for = date


class DeliveryScheduled(CancellableState):
    status = DonationIntentStatus.DELIVERY_SCHEDULED

    def mark_delivered(self, actor: Role) -> None:
        require_role(actor, Role.DONOR)
        self._move_to(Delivered)
        self._intent.delivered_at = datetime.now(UTC)


class Delivered(IntentState):
    status = DonationIntentStatus.DELIVERED

    def confirm_receipt(self, actor: Role) -> None:
        require_role(actor, Role.MANAGER)
        self._move_to(Received)
        self._intent.received_at = datetime.now(UTC)


class Received(IntentState):
    status = DonationIntentStatus.RECEIVED


class Cancelled(IntentState):
    status = DonationIntentStatus.CANCELLED


STATE_CLASS_BY_STATUS: dict[DonationIntentStatus, type[IntentState]] = {
    state.status: state
    for state in (Registered, InContact, DeliveryScheduled, Delivered, Received, Cancelled)
}


def state_of(intent: DonationIntent) -> IntentState:
    return STATE_CLASS_BY_STATUS[intent.status](intent)
