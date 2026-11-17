import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.enums import ACTIVE_INTENT_STATUSES, DonationIntentStatus
from src.models.donation_intent import UNIQUE_ACTIVE_INTENT_INDEX, DonationIntent
from src.models.need import Need
from src.models.user import Donor
from tests.models.helpers import register_intent, save_donor

OTHER_DONOR_EMAIL = "joao@exemplo.com"
FINISHED_STATUSES = sorted(set(DonationIntentStatus) - ACTIVE_INTENT_STATUSES)


def count_intents(db_session: Session) -> int:
    return db_session.scalar(select(func.count()).select_from(DonationIntent)) or 0


@pytest.mark.parametrize("status", sorted(ACTIVE_INTENT_STATUSES))
def test_a_donor_cannot_have_two_active_intents_for_the_same_need(
    db_session: Session, need: Need, donor: Donor, status: DonationIntentStatus
) -> None:
    register_intent(db_session, need, donor, status)

    with pytest.raises(IntegrityError, match=UNIQUE_ACTIVE_INTENT_INDEX):
        register_intent(db_session, need, donor)


@pytest.mark.parametrize("status", FINISHED_STATUSES)
def test_a_donor_can_show_interest_again_once_the_last_intent_is_finished(
    db_session: Session, need: Need, donor: Donor, status: DonationIntentStatus
) -> None:
    register_intent(db_session, need, donor, status)

    register_intent(db_session, need, donor)

    assert count_intents(db_session) == 2


def test_different_donors_can_each_have_an_active_intent_for_the_same_need(
    db_session: Session, need: Need, donor: Donor
) -> None:
    register_intent(db_session, need, donor)

    register_intent(db_session, need, save_donor(db_session, OTHER_DONOR_EMAIL))

    assert count_intents(db_session) == 2


def test_an_intent_requires_a_donor(db_session: Session, need: Need) -> None:
    db_session.add(DonationIntent(need=need, status=DonationIntentStatus.REGISTERED))

    with pytest.raises(IntegrityError, match="donor_id"):
        db_session.commit()
