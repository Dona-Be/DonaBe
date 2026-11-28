import pytest
from sqlalchemy.orm import Session

from src.domain.enums import Cause, Verdict
from src.domain.search import SearchPage
from src.models.institution import Institution
from src.models.user import Donor, Manager
from src.repositories.institutions import SqlAlchemyInstitutionRepository
from tests.fakes import USER_EMAIL
from tests.models.helpers import MANAGER_EMAIL, new_institution, point_at, profile

FULLWIDTH_PERCENT = chr(0xFF05)
FULLWIDTH_LOW_LINE = chr(0xFF3F)
LAR = "Lar 100% Animal"
ABRIGO = "Abrigo Amigo"
SAUDE = "Instituto Saúde Já"
# (legal name, trade name, km north of the donor, verdict, causes)
INSTITUTIONS = (
    (LAR, None, 7, Verdict.LIKELY_CHARITY, [Cause.ANIMALS]),
    (ABRIGO, "Casa São José", 3, Verdict.NONPROFIT, [Cause.ANIMALS]),
    (SAUDE, None, 0.5, Verdict.NONPROFIT, [Cause.HEALTH]),
    ("Saúde Inativa", None, 1, Verdict.INACTIVE, [Cause.HEALTH]),
    ("Saúde Improvável", None, 2, Verdict.UNLIKELY, [Cause.HEALTH]),
    ("Saúde Distante", None, 15, Verdict.LIKELY_CHARITY, [Cause.HEALTH]),
)


def save_institutions(db_session: Session) -> None:
    manager = Manager.from_profile(profile(MANAGER_EMAIL))
    for index, (legal_name, trade_name, km, verdict, causes) in enumerate(INSTITUTIONS):
        institution = new_institution(manager)
        institution.cnpj = f"{index:014d}"
        institution.legal_name = legal_name
        institution.trade_name = trade_name
        institution.location = point_at(km)
        institution.verdict = verdict
        institution.causes = causes
        db_session.add(institution)


@pytest.fixture
def donor(db_session: Session) -> Donor:
    save_institutions(db_session)
    donor = Donor.from_profile(profile(USER_EMAIL), location=point_at(0))
    db_session.add(donor)
    db_session.commit()
    return donor


def names(rows: list[tuple[Institution, float]]) -> list[str]:
    return [institution.legal_name for institution, _ in rows]


def test_list_within_hides_inactive_and_unlikely_verdicts_nearest_first_in_km(
    db_session: Session, donor: Donor
) -> None:
    rows = SqlAlchemyInstitutionRepository(db_session).list_within(donor.id, 10, page=None)

    assert names(rows) == [SAUDE, ABRIGO, LAR]
    assert [distance_km for _, distance_km in rows] == pytest.approx([0.5, 3, 7], abs=0.01)


def test_list_within_measures_the_radius_in_km_and_pages_by_distance(
    db_session: Session, donor: Donor
) -> None:
    repository = SqlAlchemyInstitutionRepository(db_session)

    assert names(repository.list_within(donor.id, 4, SearchPage(number=1, size=1))) == [SAUDE]
    assert names(repository.list_within(donor.id, 4, SearchPage(number=2, size=1))) == [ABRIGO]
    assert names(repository.list_within(donor.id, 4, SearchPage(number=3, size=1))) == []


def test_list_within_keeps_any_of_the_chosen_causes(db_session: Session, donor: Donor) -> None:
    repository = SqlAlchemyInstitutionRepository(db_session)
    causes = (Cause.ANIMALS, Cause.EDUCATION)

    assert names(repository.list_within(donor.id, 10, page=None, causes=causes)) == [ABRIGO, LAR]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("  SAÚDE ", [SAUDE]),
        ("sao jose", [ABRIGO]),
        ("%", [LAR]),
        (FULLWIDTH_PERCENT, [LAR]),
        (FULLWIDTH_LOW_LINE, []),
    ],
)
def test_list_within_finds_either_name_ignoring_case_accents_and_wildcards(
    db_session: Session, donor: Donor, name: str, expected: list[str]
) -> None:
    repository = SqlAlchemyInstitutionRepository(db_session)

    assert names(repository.list_within(donor.id, 10, page=None, name=name)) == expected
