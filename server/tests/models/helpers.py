from sqlalchemy.orm import Session

from src.domain.enums import DonationIntentStatus, NeedStatus, Verdict
from src.domain.user_profile import UserProfile
from src.models.donation_intent import DonationIntent
from src.models.institution import Association
from src.models.need import Need
from src.models.user import Donor, Manager
from tests.fakes import USER_EMAIL, USER_NAME

MANAGER_EMAIL = "gestora@exemplo.com"


def profile(email: str) -> UserProfile:
    return UserProfile(email=email, name=USER_NAME, picture_url=None)


def save_donor(db_session: Session, email: str = USER_EMAIL) -> Donor:
    donor = Donor.from_profile(profile(email))
    db_session.add(donor)
    db_session.commit()
    return donor


def save_need(db_session: Session) -> Need:
    institution = Association(
        cnpj="11222333000181",
        legal_name="Associação Amigos dos Animais",
        street="Avenida Paulista",
        number="1000",
        neighborhood="Bela Vista",
        city="São Paulo",
        state="SP",
        postal_code="01310200",
        verdict=Verdict.LIKELY_CHARITY,
        reasons=[],
        cnpj_data={},
        manager=Manager.from_profile(profile(MANAGER_EMAIL)),
    )
    need = Need(
        institution=institution,
        title="Ração",
        description="Ração para cães adultos",
        status=NeedStatus.OPEN,
    )
    db_session.add(need)
    db_session.commit()
    return need


def register_intent(
    db_session: Session,
    need: Need,
    donor: Donor,
    status: DonationIntentStatus = DonationIntentStatus.REGISTERED,
) -> DonationIntent:
    intent = DonationIntent(need=need, donor=donor, status=status)
    db_session.add(intent)
    db_session.commit()
    return intent
