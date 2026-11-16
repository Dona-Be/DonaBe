from src.domain.enums import ACTIVE_INTENT_STATUSES, DonationIntentStatus


def test_an_intent_stays_active_until_it_is_received_or_cancelled() -> None:
    finished = {DonationIntentStatus.RECEIVED, DonationIntentStatus.CANCELLED}

    assert ACTIVE_INTENT_STATUSES == set(DonationIntentStatus) - finished
