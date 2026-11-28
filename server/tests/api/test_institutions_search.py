from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.authentication import DONORS_ONLY_MESSAGE
from src.domain.enums import Cause, Verdict
from tests.api.helpers import (
    ABRIGO,
    DISTANTE,
    GOOGLE_CALLBACK,
    INSTITUTIONS_AROUND,
    LAR,
    SAUDE,
    SEARCH,
    names,
)
from tests.models.helpers import save_institutions


def test_lists_the_visible_institutions_within_10_km_nearest_first_by_default(
    located_donor_client: TestClient, db_session: Session
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = located_donor_client.get(SEARCH)

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


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"max_distance_km": 4}, [SAUDE, ABRIGO]),
        ({"max_distance_km": 20}, [SAUDE, ABRIGO, LAR, DISTANTE]),
        ({"max_distance_km": 4, "strategy": "best_match"}, [ABRIGO, SAUDE]),
    ],
)
def test_lists_only_the_institutions_within_max_distance_km(
    located_donor_client: TestClient,
    db_session: Session,
    params: dict[str, Any],
    expected: list[str],
) -> None:
    save_institutions(db_session, INSTITUTIONS_AROUND)

    response = located_donor_client.get(SEARCH, params=params)

    assert names(response) == expected


@pytest.mark.parametrize("strategy", ["nearest", "best_match", "cause_text"])
def test_each_page_has_20_institutions(
    located_donor_client: TestClient, db_session: Session, strategy: str
) -> None:
    nearest_first = tuple(
        (f"Instituição {index}", index / 10, Verdict.NONPROFIT, Cause.HEALTH) for index in range(21)
    )
    save_institutions(db_session, nearest_first)

    first_page = located_donor_client.get(SEARCH, params={"strategy": strategy})
    second_page = located_donor_client.get(SEARCH, params={"strategy": strategy, "page": 2})
    past_the_end = located_donor_client.get(SEARCH, params={"strategy": strategy, "page": 3})

    assert names(first_page) == [name for name, *_ in nearest_first[:20]]
    assert names(second_page) == ["Instituição 20"]
    assert past_the_end.json() == []


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
        {"causes": ["animals"] * (len(Cause) + 1)},
        {"cause": "animals"},
        {"q": "a" * 201},
        {"q": "a\0b"},
    ],
)
def test_rejects_invalid_parameters(
    located_donor_client: TestClient, params: dict[str, Any]
) -> None:
    response = located_donor_client.get(SEARCH, params=params)

    assert response.status_code == 422
    # A query error, so "search" was not read as an institution id
    assert [error["loc"][0] for error in response.json()["detail"]] == ["query"]


@pytest.mark.usefixtures("donor")
def test_refuses_a_donor_without_location(client: TestClient) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    response = client.get(SEARCH)

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Informe seu CEP no perfil para buscar instituições perto de você."
    }


def test_requires_a_logged_in_user(client: TestClient) -> None:
    assert client.get(SEARCH).status_code == 401


def test_refuses_a_manager(manager_client: TestClient) -> None:
    response = manager_client.get(SEARCH)

    assert response.status_code == 403
    assert response.json() == {"detail": DONORS_ONLY_MESSAGE}
