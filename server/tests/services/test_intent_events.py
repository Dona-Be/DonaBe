from src.domain.enums import DonationIntentStatus, NotificationType, Role
from src.models.donation_intent import DonationIntent
from src.services.intent_events import IntentEvent, IntentEventPublisher, IntentObserver


class FakeObserver(IntentObserver):
    def __init__(self) -> None:
        self.events: list[IntentEvent] = []

    def update(self, event: IntentEvent) -> None:
        self.events.append(event)


def registered_event() -> IntentEvent:
    status = DonationIntentStatus.REGISTERED
    intent = DonationIntent(status=status)
    return IntentEvent(NotificationType.INTENT_REGISTERED, intent, Role.DONOR, None, status)


def test_notify_sends_the_event_to_every_attached_observer() -> None:
    publisher = IntentEventPublisher()
    first, second = FakeObserver(), FakeObserver()
    publisher.attach(first)
    publisher.attach(second)
    event = registered_event()

    publisher.notify(event)

    assert first.events == [event]
    assert second.events == [event]


def test_a_detached_observer_is_no_longer_notified() -> None:
    publisher = IntentEventPublisher()
    kept, detached = FakeObserver(), FakeObserver()
    publisher.attach(kept)
    publisher.attach(detached)
    event = registered_event()

    publisher.detach(detached)
    publisher.notify(event)

    assert kept.events == [event]
    assert detached.events == []
