from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.enums import Cause, NeedStatus
from src.models.institution import Foundation, Institution
from src.models.user import Manager
from tests.api.helpers import ABRIGO, INSTITUTIONS_AROUND, LAR, SAUDE, SEARCH, names
from tests.models.helpers import (
    MANAGER_EMAIL,
    add_needs,
    new_institution,
    point_at,
    profile,
    save_institutions,
)

NONPROFIT_REASON = "CNPJ verificado: entidade sem fins lucrativos"


def test_best_match_orders_by_score_and_explains_it(
    located_donor_client: TestClient, db_session: Session
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = located_donor_client.get(SEARCH, params={"strategy": "best_match"})

    assert names(response) == [ABRIGO, SAUDE, LAR]
    abrigo, saude, _ = response.json()
    assert abrigo["distance_km"] == pytest.approx(3, abs=0.01)
    assert abrigo["score"] == 45
    assert abrigo["match_reasons"] == [
        "Fica a até 5 km de você",
        "Atende sua causa: Animais",
        NONPROFIT_REASON,
    ]
    assert saude["score"] == 40
    assert saude["match_reasons"] == ["Fica a até 2 km de você", NONPROFIT_REASON]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"causes": "animals"}, [ABRIGO]),
        ({"causes": ["animals", "elderly"]}, [ABRIGO, LAR]),
        ({"q": "lar"}, [LAR]),
        ({"q": "SAUDE"}, [SAUDE]),
        ({"causes": "animals", "q": "saude"}, []),
        ({"causes": list(Cause)}, [SAUDE, ABRIGO, LAR]),
        ({}, [SAUDE, ABRIGO, LAR]),
    ],
)
def test_cause_text_keeps_the_institutions_with_the_causes_and_the_name(
    located_donor_client: TestClient,
    db_session: Session,
    params: dict[str, Any],
    expected: list[str],
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = located_donor_client.get(SEARCH, params={"strategy": "cause_text", **params})

    assert names(response) == expected


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({}, [SAUDE, ABRIGO, LAR]),
        ({"strategy": "nearest"}, [SAUDE, ABRIGO, LAR]),
        ({"strategy": "best_match"}, [ABRIGO, SAUDE, LAR]),
    ],
)
def test_only_cause_text_uses_causes_and_q(
    located_donor_client: TestClient,
    db_session: Session,
    params: dict[str, str],
    expected: list[str],
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = located_donor_client.get(SEARCH, params={**params, "causes": "health", "q": "saude"})

    assert names(response) == expected


@pytest.mark.parametrize("strategy", ["nearest", "best_match", "cause_text"])
def test_each_result_counts_its_open_needs(
    located_donor_client: TestClient, db_session: Session, strategy: str
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)
    saude = db_session.scalars(select(Institution).where(Institution.legal_name == SAUDE)).one()
    statuses = (NeedStatus.OPEN, NeedStatus.OPEN, NeedStatus.FULFILLED, NeedStatus.CLOSED)
    add_needs(db_session, saude, *statuses)

    response = located_donor_client.get(SEARCH, params={"strategy": strategy})

    counts = {found["legal_name"]: found["open_needs_count"] for found in response.json()}
    assert counts == {SAUDE: 2, ABRIGO: 0, LAR: 0}


def test_each_result_shows_the_type_names_causes_and_verdict_of_its_institution(
    located_donor_client: TestClient, db_session: Session
) -> None:
    foundation = new_institution(Manager.from_profile(profile(MANAGER_EMAIL)), Foundation)
    foundation.legal_name = "Fundação Viva Bem"
    foundation.trade_name = "Viva Bem"
    foundation.causes = [Cause.ELDERLY, Cause.WOMEN]
    foundation.location = point_at(1)
    db_session.add(foundation)
    db_session.commit()

    [found] = located_donor_client.get(SEARCH).json()

    assert found["id"] == foundation.id
    assert found["type"] == "foundation"
    assert found["legal_name"] == "Fundação Viva Bem"
    assert found["trade_name"] == "Viva Bem"
    assert found["causes"] == ["elderly", "women"]
    assert found["verdict"] == "likely_charity"
