from types import SimpleNamespace
from typing import Any

import pytest

from src.api.error_handlers import status_for
from src.domain.enums import Cause, Verdict
from src.domain.exceptions import InvalidSearchStrategyError
from src.domain.search import SearchFilters, SearchPage
from src.models.user import Donor
from src.services.search_strategies import (
    BestMatchStrategy,
    CauseTextStrategy,
    InstitutionSearchService,
    NearestStrategy,
    SearchResult,
)

DONOR_ID = 12
RADIUS_KM = 8
FIRST_PAGE = SearchPage()
FILTERS = SearchFilters(radius_km=RADIUS_KM, causes=(Cause.HEALTH,), name="lar")


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


def test_nearest_strategy_asks_for_the_radius_and_page_without_text_filters() -> None:
    closest = make_institution(1)
    farther = make_institution(2)
    repository = FakeInstitutionRepository([(closest, 0.8), (farther, 1.2)])
    page = SearchPage(number=1, size=2)

    results = NearestStrategy(repository).search(make_donor(), FILTERS, page)

    assert repository.calls == [(DONOR_ID, RADIUS_KM, page, (), None)]
    assert results == [SearchResult(closest, 0.8), SearchResult(farther, 1.2)]


def test_best_match_scores_all_candidates_sorts_and_then_pages() -> None:
    charity_7km = make_institution(1, Cause.ANIMALS)
    nonprofit_3km = make_institution(2, Cause.ANIMALS, verdict=Verdict.NONPROFIT)
    other_cause_500m = make_institution(3, Cause.HEALTH, verdict=Verdict.NONPROFIT)
    repository = FakeInstitutionRepository(
        [(other_cause_500m, 0.5), (nonprofit_3km, 3), (charity_7km, 7)]
    )
    strategy = BestMatchStrategy(repository)
    donor = make_donor(Cause.ANIMALS)

    first_page = strategy.search(donor, FILTERS, SearchPage(number=1, size=2))
    second_page = strategy.search(donor, FILTERS, SearchPage(number=2, size=2))

    # 45 points at 3 km and at 7 km (the nearer wins the tie), 40 at 0.5 km
    assert [result.institution for result in first_page] == [nonprofit_3km, charity_7km]
    assert second_page == [
        SearchResult(
            other_cause_500m,
            0.5,
            40,
            ("Fica a até 2 km de você", "CNPJ verificado: entidade sem fins lucrativos"),
        )
    ]
    assert repository.calls[0] == (DONOR_ID, RADIUS_KM, None, (), None)


def test_cause_text_passes_its_causes_and_name_to_the_repository() -> None:
    institution = make_institution(1, Cause.HEALTH)
    repository = FakeInstitutionRepository([(institution, 0.8)])

    results = CauseTextStrategy(repository).search(make_donor(), FILTERS, FIRST_PAGE)

    assert repository.calls == [(DONOR_ID, RADIUS_KM, FIRST_PAGE, (Cause.HEALTH,), "lar")]
    assert results == [SearchResult(institution, 0.8)]


@pytest.mark.parametrize(
    ("name", "call"),
    [
        ("nearest", (DONOR_ID, RADIUS_KM, FIRST_PAGE, (), None)),
        ("best_match", (DONOR_ID, RADIUS_KM, None, (), None)),
        ("cause_text", (DONOR_ID, RADIUS_KM, FIRST_PAGE, (Cause.HEALTH,), "lar")),
    ],
)
def test_registry_selects_each_strategy_by_registered_name(
    name: str, call: tuple[Any, ...]
) -> None:
    repository = FakeInstitutionRepository()

    InstitutionSearchService(repository).search(make_donor(), name, FILTERS, FIRST_PAGE)

    assert repository.calls == [call]


def test_registry_rejects_unknown_name_with_an_error_mapped_to_422() -> None:
    service = InstitutionSearchService(FakeInstitutionRepository())

    with pytest.raises(InvalidSearchStrategyError, match="não é válida") as error:
        service.search(make_donor(), "unknown", SearchFilters(), SearchPage())

    assert status_for(error.value) == 422
