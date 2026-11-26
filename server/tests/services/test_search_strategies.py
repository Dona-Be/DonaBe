from types import SimpleNamespace
from typing import Any

import pytest

from src.api.error_handlers import status_for
from src.domain.enums import Cause, Verdict
from src.domain.exceptions import InvalidSearchStrategyError
from src.domain.search import SearchFilters, SearchPage
from src.models.user import Donor
from src.services.search_strategies import (
    STRATEGY_BEST_MATCH,
    STRATEGY_CAUSE_TEXT,
    STRATEGY_NEAREST,
    BestMatchStrategy,
    CauseTextStrategy,
    InstitutionSearchService,
    NearestStrategy,
)

DONOR_ID = 12


class FakeInstitutionRepository:
    def __init__(self, rows: list[tuple[Any, float]] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[tuple[Any, ...]] = []

    def list_within(
        self,
        donor_id: int,
        radius_km: float,
        page: SearchPage | None,
        *,
        causes: tuple[Cause, ...] = (),
        name: str | None = None,
    ) -> list[tuple[Any, float]]:
        self.calls.append((donor_id, radius_km, page, causes, name))
        if page is None:
            return self.rows
        return self.rows[page.offset : page.offset + page.size]


def make_donor(*causes: Cause) -> Donor:
    return Donor(id=DONOR_ID, postal_code="01310200", preferred_causes=list(causes))


def make_institution(
    institution_id: int,
    *causes: Cause,
    verdict: Verdict = Verdict.LIKELY_CHARITY,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=institution_id,
        causes=list(causes),
        verdict=verdict,
        postal_code="01310200",
    )


def test_nearest_strategy_filters_to_radius_orders_by_distance_and_pages() -> None:
    closest = make_institution(1)
    farther = make_institution(2)
    repository = FakeInstitutionRepository([(closest, 0.8), (farther, 1.2)])
    strategy = NearestStrategy(repository)
    page = SearchPage(number=1, size=2)

    results = strategy.search(make_donor(), SearchFilters(radius_km=4), page)

    assert repository.calls == [(DONOR_ID, 4, page, (), None)]
    assert results == [closest, farther]


def test_best_match_scores_all_candidates_sorts_and_then_pages() -> None:
    preferred = make_institution(1, Cause.ANIMALS)
    likely = make_institution(2)
    nonprofit = make_institution(3, verdict=Verdict.NONPROFIT)
    repository = FakeInstitutionRepository([(nonprofit, 7), (likely, 1), (preferred, 1)])
    strategy = BestMatchStrategy(repository)

    results = strategy.search(
        make_donor(Cause.ANIMALS), SearchFilters(), SearchPage(number=1, size=2)
    )

    assert repository.calls == [(DONOR_ID, 10, None, (), None)]
    assert results == [preferred, likely]


def test_cause_text_uses_gin_array_overlap_and_accent_insensitive_name_search() -> None:
    first = make_institution(1, Cause.HEALTH)
    second = make_institution(2, Cause.ANIMALS)
    repository = FakeInstitutionRepository([(first, 0.8), (second, 1.2)])
    strategy = CauseTextStrategy(repository)
    causes = (Cause.HEALTH, Cause.ANIMALS)

    results = strategy.search(
        make_donor(), SearchFilters(causes=causes, name="  SAÚDE  "), SearchPage()
    )

    assert repository.calls == [(DONOR_ID, 10, SearchPage(), causes, "  SAÚDE  ")]
    assert results == [first, second]


def test_registry_selects_each_strategy_by_registered_name() -> None:
    repository = FakeInstitutionRepository()
    service = InstitutionSearchService(repository)

    for name in (STRATEGY_NEAREST, STRATEGY_BEST_MATCH, STRATEGY_CAUSE_TEXT):
        service.search(make_donor(), name, SearchFilters(), SearchPage())

    assert len(repository.calls) == 3


def test_registry_rejects_unknown_name_with_an_error_mapped_to_422() -> None:
    service = InstitutionSearchService(FakeInstitutionRepository())

    with pytest.raises(InvalidSearchStrategyError, match="não é válida") as error:
        service.search(make_donor(), "unknown", SearchFilters(), SearchPage())

    assert status_for(error.value) == 422
