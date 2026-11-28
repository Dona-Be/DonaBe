from typing import Any

import pytest

from src.api.error_handlers import status_for
from src.domain.enums import Cause, SearchStrategyName
from src.domain.exceptions import DonorWithoutLocationError, InvalidSearchStrategyError
from src.domain.search import SearchPage
from src.services.search_strategies import InstitutionSearchService
from tests.services.helpers import (
    DONOR_ID,
    FILTERS,
    FIRST_PAGE,
    RADIUS_KM,
    FakeInstitutionRepository,
    FakeNeedRepository,
    make_donor,
    make_institution,
)


@pytest.mark.parametrize(
    ("name", "call"),
    [
        ("nearest", (DONOR_ID, RADIUS_KM, FIRST_PAGE, (), None)),
        ("best_match", (DONOR_ID, RADIUS_KM)),
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
    donor = make_donor()

    with pytest.raises(InvalidSearchStrategyError, match="não é válida") as error:
        service.search(donor, "unknown", FILTERS, FIRST_PAGE)

    assert status_for(error.value) == 422


@pytest.mark.parametrize("name", list(SearchStrategyName))
def test_refuses_a_donor_without_location_before_searching(name: SearchStrategyName) -> None:
    repository = FakeInstitutionRepository()
    service = InstitutionSearchService(repository, FakeNeedRepository())
    donor = make_donor()
    donor.location = None

    with pytest.raises(DonorWithoutLocationError, match="Informe seu CEP") as error:
        service.search(donor, name, FILTERS, FIRST_PAGE)

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
