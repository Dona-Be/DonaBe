from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import Select

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


class FakeInstitutionRepository:
    def __init__(self, rows: list[tuple[Any, ...]] | None = None) -> None:
        self.rows = rows or []
        self.query: Select[Any] | None = None
        self.page: SearchPage | None = None
        self.calls = 0

    def search(self, query: Select[Any], page: SearchPage | None = None) -> list[tuple[Any, ...]]:
        self.calls += 1
        self.query = query
        self.page = page
        if page is None:
            return self.rows
        return self.rows[page.offset : page.offset + page.size]


def make_donor(*causes: Cause) -> Donor:
    return Donor(id=12, postal_code="01310200", preferred_causes=list(causes))


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


def compiled_query(repository: FakeInstitutionRepository) -> str:
    assert repository.query is not None
    return str(repository.query.compile(dialect=postgresql.dialect()))


def test_nearest_strategy_filters_to_radius_orders_by_distance_and_pages() -> None:
    closest = make_institution(1)
    farther = make_institution(2)
    repository = FakeInstitutionRepository([(closest, 800), (farther, 1_200)])
    strategy = NearestStrategy(repository)
    page = SearchPage(number=1, size=2)

    results = strategy.search(make_donor(), SearchFilters(radius_km=4), page)

    sql = compiled_query(repository)
    assert "ST_DWithin" in sql
    assert "ORDER BY ST_Distance" in sql
    assert "institutions.verdict NOT IN" not in sql
    assert repository.page == page
    assert results == [closest, farther]


def test_best_match_scores_all_candidates_sorts_and_then_pages() -> None:
    preferred = make_institution(1, Cause.ANIMALS)
    likely = make_institution(2)
    nonprofit = make_institution(3, verdict=Verdict.NONPROFIT)
    repository = FakeInstitutionRepository(
        [(nonprofit, 7_000), (likely, 1_000), (preferred, 1_000)]
    )
    strategy = BestMatchStrategy(repository)

    results = strategy.search(
        make_donor(Cause.ANIMALS), SearchFilters(), SearchPage(number=1, size=2)
    )

    assert repository.page is None
    assert results == [preferred, likely]
    assert repository.query is not None
    assert "ST_DWithin" in compiled_query(repository)


def test_cause_text_uses_gin_array_overlap_and_accent_insensitive_name_search() -> None:
    first = make_institution(1, Cause.HEALTH)
    second = make_institution(2, Cause.ANIMALS)
    repository = FakeInstitutionRepository([(first, 800), (second, 1_200)])
    strategy = CauseTextStrategy(repository)

    results = strategy.search(
        make_donor(),
        SearchFilters(causes=(Cause.HEALTH, Cause.ANIMALS), name="  SAÚDE  "),
        SearchPage(),
    )

    sql = compiled_query(repository)
    assert "institutions.causes &&" in sql
    assert repository.query.compile(dialect=postgresql.dialect()).params["causes_1"] == [
        Cause.HEALTH,
        Cause.ANIMALS,
    ]
    assert "unaccent(lower(institutions.legal_name))" in sql
    assert "unaccent(lower(coalesce(institutions.trade_name" in sql
    assert repository.page == SearchPage()
    assert results == [first, second]


def test_registry_selects_each_strategy_by_registered_name() -> None:
    repository = FakeInstitutionRepository()
    service = InstitutionSearchService(repository)

    for name in (STRATEGY_NEAREST, STRATEGY_BEST_MATCH, STRATEGY_CAUSE_TEXT):
        service.search(make_donor(), name, SearchFilters(), SearchPage())

    assert repository.calls == 3


def test_registry_rejects_unknown_name_with_an_error_mapped_to_422() -> None:
    service = InstitutionSearchService(FakeInstitutionRepository())

    with pytest.raises(InvalidSearchStrategyError, match="não é válida") as error:
        service.search(make_donor(), "unknown", SearchFilters(), SearchPage())

    assert status_for(error.value) == 422
