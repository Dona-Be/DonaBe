from typing import Any

from geoalchemy2 import WKTElement
from sqlalchemy.orm import Session

from src.domain.enums import DonationIntentStatus, NeedStatus, Verdict
from src.domain.user_profile import UserProfile
from src.models.donation_intent import DonationIntent
from src.models.institution import WGS84_SRID, Association, Institution
from src.models.need import Need
from src.models.user import Donor, Manager
from tests.fakes import USER_EMAIL, USER_NAME

MANAGER_EMAIL = "gestora@exemplo.com"
DONOR_LATITUDE = -23.55
DONOR_LONGITUDE = -46.63
KM_PER_DEGREE_OF_LATITUDE = 110.75


def profile(email: str) -> UserProfile:
    return UserProfile(email=email, name=USER_NAME, picture_url=None)


def point_at(km_north: float) -> WKTElement:
    latitude = DONOR_LATITUDE + km_north / KM_PER_DEGREE_OF_LATITUDE
    return WKTElement(f"POINT({DONOR_LONGITUDE} {latitude})", srid=WGS84_SRID)


def save_donor(db_session: Session, email: str = USER_EMAIL) -> Donor:
    donor = Donor.from_profile(profile(email))
    db_session.add(donor)
    db_session.commit()
    return donor


def new_institution(manager: Manager, kind: type[Institution] = Association) -> Institution:
    return kind(
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
        manager=manager,
    )


def save_need(db_session: Session) -> Need:
    need = Need(
        institution=new_institution(Manager.from_profile(profile(MANAGER_EMAIL))),
        title="Ração",
        description="Ração para cães adultos",
        status=NeedStatus.OPEN,
    )
    db_session.add(need)
    db_session.commit()
    return need


def add_needs(db_session: Session, institution: Institution, *statuses: NeedStatus) -> None:
    for status in statuses:
        db_session.add(
            Need(institution=institution, title="Cobertores", description="Doação", status=status)
        )
    db_session.commit()


def save_institutions(db_session: Session, around: tuple[tuple[Any, ...], ...]) -> None:
    manager = Manager.from_profile(profile(MANAGER_EMAIL))
    for index, (legal_name, km, verdict, cause) in enumerate(around):
        institution = new_institution(manager)
        institution.cnpj = f"{index:014d}"
        institution.legal_name = legal_name
        institution.location = None if km is None else point_at(km)
        institution.verdict = verdict
        institution.causes = [cause]
        db_session.add(institution)
    db_session.commit()


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
