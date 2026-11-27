from types import SimpleNamespace
from typing import Any

import pytest
from geoalchemy2 import WKTElement

from src.api.error_handlers import status_for
from src.domain.enums import Cause, SearchStrategyName, Verdict
from src.domain.exceptions import DonorWithoutLocationError, InvalidSearchStrategyError
from src.domain.search import SearchFilters, SearchPage
from src.models.institution import WGS84_SRID
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


class FakeNeedRepository:
    def __init__(self, open_needs: dict[int, int] | None = None) -> None:
        self.open_needs = open_needs or {}
        self.calls: list[list[int]] = []

    def count_open_by_institution(self, institution_ids: list[int]) -> dict[int, int]:
        self.calls.append(list(institution_ids))
        return {key: value for key, value in self.open_needs.items() if key in institution_ids}


def make_donor(*causes: Cause) -> Donor:
    return Donor(
        id=DONOR_ID,
        postal_code="01310200",
        location=WKTElement("POINT(-46.63 -23.55)", srid=WGS84_SRID),
        preferred_causes=list(causes),
    )


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

    InstitutionSearchService(repository, FakeNeedRepository()).search(
        make_donor(), name, FILTERS, FIRST_PAGE
    )

    assert repository.calls == [call]


@pytest.mark.parametrize("name", list(SearchStrategyName))
def test_registry_has_a_strategy_for_every_name_of_the_enum(name: SearchStrategyName) -> None:
    repository = FakeInstitutionRepository()

    InstitutionSearchService(repository, FakeNeedRepository()).search(
        make_donor(), name, FILTERS, FIRST_PAGE
    )

    assert len(repository.calls) == 1


def test_registry_rejects_unknown_name_with_an_error_mapped_to_422() -> None:
    service = InstitutionSearchService(FakeInstitutionRepository(), FakeNeedRepository())

    with pytest.raises(InvalidSearchStrategyError, match="não é válida") as error:
        service.search(make_donor(), "unknown", SearchFilters(), SearchPage())

    assert status_for(error.value) == 422


@pytest.mark.parametrize("name", list(SearchStrategyName))
def test_refuses_a_donor_without_location_before_searching(name: SearchStrategyName) -> None:
    repository = FakeInstitutionRepository()
    donor = make_donor()
    donor.location = None

    with pytest.raises(DonorWithoutLocationError, match="Informe seu CEP") as error:
        InstitutionSearchService(repository, FakeNeedRepository()).search(
            donor, name, FILTERS, FIRST_PAGE
        )

    assert status_for(error.value) == 422
    assert repository.calls == []


def test_counts_the_open_needs_of_the_page_only_in_one_call() -> None:
    institutions = [make_institution(institution_id) for institution_id in (1, 2, 3)]
    repository = FakeInstitutionRepository([(institution, 1) for institution in institutions])
    needs = FakeNeedRepository({1: 4, 3: 2})
    service = InstitutionSearchService(repository, needs)

    results = service.search(make_donor(), "best_match", FILTERS, SearchPage(number=1, size=2))

    # best_match scores all three candidates, but only the page is counted.
    assert needs.calls == [[1, 2]]
    assert [result.open_needs_count for result in results] == [4, 0]
