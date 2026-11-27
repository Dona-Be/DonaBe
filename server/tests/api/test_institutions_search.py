from typing import Any

import pytest
from fastapi.testclient import TestClient
from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.authentication import DONORS_ONLY_MESSAGE
from src.domain.enums import Cause, NeedStatus, Verdict
from src.models.institution import WGS84_SRID, Institution
from src.models.need import Need
from src.models.user import Donor, Manager
from tests.api.helpers import GOOGLE_CALLBACK, INSTITUTIONS
from tests.fakes import USER_EMAIL
from tests.models.helpers import MANAGER_EMAIL, new_institution, profile

SEARCH = f"{INSTITUTIONS}/search"
DONOR_LATITUDE = -23.55
DONOR_LONGITUDE = -46.63
KM_PER_DEGREE_OF_LATITUDE = 110.75
SAUDE = "Instituto Saúde Já"
ABRIGO = "Abrigo Amigo"
LAR = "Lar dos Idosos"
DISTANTE = "Saúde Distante"
NONPROFIT_REASON = "CNPJ verificado: entidade sem fins lucrativos"
# (legal name, km north of the donor or None without location, verdict, cause)
INSTITUTIONS_AROUND = (
    (LAR, 7, Verdict.LIKELY_CHARITY, Cause.ELDERLY),
    (ABRIGO, 3, Verdict.NONPROFIT, Cause.ANIMALS),
    (SAUDE, 0.5, Verdict.NONPROFIT, Cause.HEALTH),
    ("Saúde Inativa", 1, Verdict.INACTIVE, Cause.HEALTH),
    ("Saúde Improvável", 2, Verdict.UNLIKELY, Cause.HEALTH),
    ("Sem Localização", None, Verdict.LIKELY_CHARITY, Cause.HEALTH),
    (DISTANTE, 15, Verdict.LIKELY_CHARITY, Cause.HEALTH),
)


def point_at(km_north: float) -> WKTElement:
    latitude = DONOR_LATITUDE + km_north / KM_PER_DEGREE_OF_LATITUDE
    return WKTElement(f"POINT({DONOR_LONGITUDE} {latitude})", srid=WGS84_SRID)


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


def log_in(client: TestClient) -> TestClient:
    # The user is already registered, so the Google login starts the session.
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    return client


@pytest.fixture
def donor_client(client: TestClient, db_session: Session) -> TestClient:
    donor = Donor.from_profile(
        profile(USER_EMAIL),
        postal_code="01310200",
        location=point_at(0),
        preferred_causes=[Cause.ANIMALS],
    )
    db_session.add(donor)
    db_session.commit()
    return log_in(client)


def names(response: Any) -> list[str]:
    return [found["legal_name"] for found in response.json()]


def test_nearest_is_the_default_and_lists_the_closest_visible_institutions_first(
    donor_client: TestClient, db_session: Session
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = donor_client.get(SEARCH)

    assert response.status_code == 200
    assert names(response) == [SAUDE, ABRIGO, LAR]
    closest = response.json()[0]
    assert closest.pop("distance_km") == pytest.approx(0.5, abs=0.01)
    assert closest == {
        "id": 3,
        "type": "association",
        "legal_name": SAUDE,
        "trade_name": None,
        "causes": ["health"],
        "verdict": "nonprofit",
        "score": None,
        "match_reasons": [],
        "open_needs_count": 0,
    }


def test_the_strategy_can_be_chosen_by_name(donor_client: TestClient, db_session: Session) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = donor_client.get(SEARCH, params={"strategy": "nearest"})

    assert names(response) == [SAUDE, ABRIGO, LAR]


@pytest.mark.parametrize(
    ("max_distance_km", "expected"),
    [(4, [SAUDE, ABRIGO]), (20, [SAUDE, ABRIGO, LAR, DISTANTE])],
)
def test_lists_only_the_institutions_within_max_distance_km(
    donor_client: TestClient, db_session: Session, max_distance_km: float, expected: list[str]
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = donor_client.get(SEARCH, params={"max_distance_km": max_distance_km})

    assert names(response) == expected


@pytest.mark.parametrize("strategy", ["nearest", "best_match", "cause_text"])
def test_each_page_has_20_institutions(
    donor_client: TestClient, db_session: Session, strategy: str
) -> None:
    nearest_first = tuple(
        (f"Instituição {km}", km / 10, Verdict.NONPROFIT, Cause.HEALTH) for km in range(21)
    )
    save_institutions(db_session, nearest_first)

    first_page = donor_client.get(SEARCH, params={"strategy": strategy})
    second_page = donor_client.get(SEARCH, params={"strategy": strategy, "page": 2})

    assert names(first_page) == [name for name, *_ in nearest_first[:20]]
    assert names(second_page) == ["Instituição 20"]


@pytest.mark.parametrize(
    "params",
    [
        {"strategy": "unknown"},
        {"max_distance_km": 0},
        {"max_distance_km": -1},
        {"max_distance_km": 20.5},
        {"max_distance_km": "nan"},
        {"page": 0},
        {"page": 2**31},
        {"causes": "unknown"},
        {"q": "a" * 201},
        {"q": "a\0b"},
    ],
)
def test_rejects_invalid_parameters(donor_client: TestClient, params: dict[str, Any]) -> None:
    response = donor_client.get(SEARCH, params=params)

    assert response.status_code == 422
    # The error is about the query, so "search" was not read as an institution id.
    assert [error["loc"][0] for error in response.json()["detail"]] == ["query"]


def test_best_match_orders_by_score_and_explains_it(
    donor_client: TestClient, db_session: Session
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = donor_client.get(SEARCH, params={"strategy": "best_match"})

    assert names(response) == [ABRIGO, SAUDE, LAR]
    abrigo, saude, _ = response.json()
    assert (abrigo["score"], abrigo["match_reasons"]) == (
        45,
        ["Fica a até 5 km de você", "Atende sua causa: Animais", NONPROFIT_REASON],
    )
    assert (saude["score"], saude["match_reasons"]) == (
        40,
        ["Fica a até 2 km de você", NONPROFIT_REASON],
    )


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"causes": "animals"}, [ABRIGO]),
        ({"causes": ["animals", "elderly"]}, [ABRIGO, LAR]),
        ({"q": "lar"}, [LAR]),
        ({"q": "SAUDE"}, [SAUDE]),
        ({"causes": "animals", "q": "saude"}, []),
        ({}, [SAUDE, ABRIGO, LAR]),
    ],
)
def test_cause_text_keeps_the_institutions_with_the_causes_and_the_name(
    donor_client: TestClient, db_session: Session, params: dict[str, Any], expected: list[str]
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = donor_client.get(SEARCH, params={"strategy": "cause_text", **params})

    assert names(response) == expected


@pytest.mark.parametrize(
    ("strategy", "expected"),
    [("nearest", [SAUDE, ABRIGO, LAR]), ("best_match", [ABRIGO, SAUDE, LAR])],
)
def test_only_cause_text_uses_causes_and_q(
    donor_client: TestClient, db_session: Session, strategy: str, expected: list[str]
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = donor_client.get(
        SEARCH, params={"strategy": strategy, "causes": "health", "q": "saude"}
    )

    assert names(response) == expected


@pytest.mark.parametrize("strategy", ["nearest", "best_match", "cause_text"])
def test_each_result_counts_its_open_needs(
    donor_client: TestClient, db_session: Session, strategy: str
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)
    saude = db_session.scalars(select(Institution).where(Institution.legal_name == SAUDE)).one()
    for status in (NeedStatus.OPEN, NeedStatus.OPEN, NeedStatus.FULFILLED, NeedStatus.CLOSED):
        db_session.add(Need(institution=saude, title="Luvas", description="Doação", status=status))
    db_session.commit()

    response = donor_client.get(SEARCH, params={"strategy": strategy})

    counts = {found["legal_name"]: found["open_needs_count"] for found in response.json()}
    assert counts == {SAUDE: 2, ABRIGO: 0, LAR: 0}


@pytest.mark.parametrize("strategy", ["nearest", "best_match", "cause_text"])
def test_refuses_a_donor_without_location(
    client: TestClient, db_session: Session, strategy: str
) -> None:
    db_session.add(Donor.from_profile(profile(USER_EMAIL)))
    db_session.commit()

    response = log_in(client).get(SEARCH, params={"strategy": strategy})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Informe seu CEP no perfil para buscar instituições perto de você."
    }


def test_requires_a_logged_in_user(client: TestClient) -> None:
    assert client.get(SEARCH).status_code == 401


def test_refuses_a_manager(client: TestClient, db_session: Session) -> None:
    db_session.add(Manager.from_profile(profile(USER_EMAIL)))
    db_session.commit()

    response = log_in(client).get(SEARCH)

    assert response.status_code == 403
    assert response.json() == {"detail": DONORS_ONLY_MESSAGE}
