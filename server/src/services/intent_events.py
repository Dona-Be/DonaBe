from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.enums import DonationIntentStatus, NotificationType, Role
from src.models.donation_intent import DonationIntent
from src.models.notification import Notification
from src.repositories.notifications import NotificationRepository

MANAGER_MESSAGES = {
    NotificationType.INTENT_REGISTERED: "{donor} quer doar para a necessidade {need}.",
    NotificationType.INTENT_CANCELLED: "{donor} cancelou a doação para a necessidade {need}.",
    NotificationType.INTENT_DELIVERED: (
        "{donor} marcou como entregue a doação para a necessidade {need}."
    ),
}
DONOR_MESSAGE = "Sua doação para a necessidade {need} mudou para {status}."
STATUS_LABELS = {
    DonationIntentStatus.IN_CONTACT: "Em contato",
    DonationIntentStatus.DELIVERY_SCHEDULED: "Entrega agendada",
    DonationIntentStatus.RECEIVED: "Recebida",
    DonationIntentStatus.CANCELLED: "Cancelada",
}


@dataclass(frozen=True)
class IntentEvent:
    type: NotificationType
    intent: DonationIntent
    actor: Role
    previous_status: DonationIntentStatus | None
    new_status: DonationIntentStatus


class IntentObserver(ABC):
    @abstractmethod
    def update(self, event: IntentEvent) -> None: ...


class IntentEventPublisher:
    def __init__(self) -> None:
        self._observers: list[IntentObserver] = []

    def attach(self, observer: IntentObserver) -> None:
        self._observers.append(observer)

    def detach(self, observer: IntentObserver) -> None:
        self._observers.remove(observer)

    def notify(self, event: IntentEvent) -> None:
        for observer in self._observers:
            observer.update(event)


class ManagerNotificationObserver(IntentObserver):
    def __init__(self, notifications: NotificationRepository) -> None:
        self._notifications = notifications

    def update(self, event: IntentEvent) -> None:
        if event.actor != Role.DONOR:
            return
        intent = event.intent
        template = MANAGER_MESSAGES[event.type]
        self._notifications.save(
            Notification(
                recipient=intent.need.institution.manager,
                type=event.type,
                donation_intent=intent,
                message=template.format(donor=intent.donor.name, need=intent.need.title),
            )
        )


class DonorNotificationObserver(IntentObserver):
    def __init__(self, notifications: NotificationRepository) -> None:
        self._notifications = notifications

    def update(self, event: IntentEvent) -> None:
        if event.actor != Role.MANAGER:
            return
        intent = event.intent
        status = STATUS_LABELS[event.new_status]
        self._notifications.save(
            Notification(
                recipient=intent.donor,
                type=event.type,
                donation_intent=intent,
                message=DONOR_MESSAGE.format(need=intent.need.title, status=status),
            )
        )
