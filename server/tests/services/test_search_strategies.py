import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.error_handlers import status_for
from src.domain.enums import Cause, Verdict
from src.domain.exceptions import UnknownSearchStrategyError
from src.domain.search import SearchFilters
from src.models.institution import Institution
from src.repositories.institutions import SqlAlchemyInstitutionRepository
from src.services.search_strategies import (
    BestMatchStrategy,
    CauseTextStrategy,
    NearestStrategy,
    SearchStrategy,
    strategy_named,
)
from tests.services.helpers import DONOR_CAUSE, at_km, names, save_institutions, search

ALL_STRATEGIES = [NearestStrategy, BestMatchStrategy, CauseTextStrategy]
UNMATCHED_CAUSES = (Cause.ANIMALS,)
UNMATCHED_NAME = "nenhuma"
UNUSED_REPOSITORY = SqlAlchemyInstitutionRepository(Session())


def test_nearest_lists_the_institutions_inside_the_radius_nearest_first(
    db_session: Session,
) -> None:
    save_institutions(db_session, at_km("Três km", 3), at_km("Um km", 1), at_km("Oito km", 8))

    results = search(db_session, NearestStrategy, SearchFilters(max_distance_km=5))

    assert names(results) == ["Um km", "Três km"]
    assert [result.distance_km for result in results] == pytest.approx([1, 3], abs=0.01)


def test_nearest_ignores_the_causes_and_the_name(db_session: Session) -> None:
    save_institutions(db_session, at_km("Um km", 1), at_km("Dois km", 2))
    filters = SearchFilters(causes=UNMATCHED_CAUSES, text=UNMATCHED_NAME)

    assert names(search(db_session, NearestStrategy, filters)) == ["Um km", "Dois km"]


def test_best_match_lists_the_highest_score_first_with_its_reasons(db_session: Session) -> None:
    save_institutions(
        db_session,
        at_km("Mais longe", 40, verdict=Verdict.NONPROFIT),
        at_km("Perto", 1, verdict=Verdict.NONPROFIT),
        at_km("Idosos", 8, causes=[DONOR_CAUSE]),
        at_km("Longe", 30, verdict=Verdict.NONPROFIT),
    )

    results = search(db_session, BestMatchStrategy, SearchFilters())

    assert names(results) == ["Idosos", "Perto", "Longe", "Mais longe"]
    assert [result.score for result in results] == [45, 40, 10, 10]
    assert results[0].reasons == (
        "Fica a até 10 km de você",
        "Atende sua causa: Idosos",
        "CNPJ verificado: provável instituição beneficente",
    )
    assert results[0].distance_km == pytest.approx(8, abs=0.01)


def test_best_match_scores_only_inside_the_radius_ignoring_causes_and_name(
    db_session: Session,
) -> None:
    save_institutions(db_session, at_km("Perto", 1), at_km("Oito km", 8))
    filters = SearchFilters(max_distance_km=5, causes=UNMATCHED_CAUSES, text=UNMATCHED_NAME)

    assert names(search(db_session, BestMatchStrategy, filters)) == ["Perto"]


@pytest.mark.parametrize("strategy", ALL_STRATEGIES)
def test_each_page_holds_twenty_institutions(
    db_session: Session, strategy: type[SearchStrategy]
) -> None:
    save_institutions(db_session, *(at_km(f"A {km} km", km) for km in range(31, 10, -1)))

    first_page = search(db_session, strategy, SearchFilters())
    second_page = search(db_session, strategy, SearchFilters(), page=2)

    assert names(first_page) == [f"A {km} km" for km in range(11, 31)]
    assert names(second_page) == ["A 31 km"]


@pytest.mark.parametrize("strategy", ALL_STRATEGIES)
def test_institutions_at_the_same_place_keep_the_registration_order(
    db_session: Session, strategy: type[SearchStrategy]
) -> None:
    save_institutions(db_session, at_km("Primeira", 1), at_km("Segunda", 1))
    # Editing the first one rewrites its row after the second one in the table
    first = db_session.scalar(select(Institution).where(Institution.legal_name == "Primeira"))
    first.description = "Editada"
    db_session.commit()

    assert names(search(db_session, strategy, SearchFilters())) == ["Primeira", "Segunda"]


@pytest.mark.parametrize("strategy", ALL_STRATEGIES)
def test_inactive_unlikely_and_unlocated_institutions_never_appear(
    db_session: Session, strategy: type[SearchStrategy]
) -> None:
    save_institutions(
        db_session,
        at_km("Inativa", 1, verdict=Verdict.INACTIVE),
        at_km("Improvável", 2, verdict=Verdict.UNLIKELY),
        {"legal_name": "Sem localização", "location": None},
        at_km("Beneficente", 3),
        at_km("Sem fins lucrativos", 4, verdict=Verdict.NONPROFIT),
    )

    results = search(db_session, strategy, SearchFilters())

    assert names(results) == ["Beneficente", "Sem fins lucrativos"]


@pytest.mark.parametrize(
    ("name", "strategy"),
    [
        ("nearest", NearestStrategy),
        ("best_match", BestMatchStrategy),
        ("cause_text", CauseTextStrategy),
    ],
)
def test_each_strategy_is_registered_by_name(name: str, strategy: type[SearchStrategy]) -> None:
    assert isinstance(strategy_named(name, UNUSED_REPOSITORY), strategy)


def test_an_unknown_strategy_name_is_unprocessable() -> None:
    with pytest.raises(
        UnknownSearchStrategyError, match="nearest, best_match, cause_text"
    ) as error:
        strategy_named("closest", UNUSED_REPOSITORY)

    assert status_for(error.value) == status.HTTP_422_UNPROCESSABLE_CONTENT
