from src.domain.enums import Cause, Verdict
from src.domain.search import SearchPage
from src.services.search_strategies import (
    BestMatchStrategy,
    CauseTextStrategy,
    NearestStrategy,
    SearchResult,
)
from tests.services.helpers import (
    DONOR_ID,
    FILTERS,
    FIRST_PAGE,
    RADIUS_KM,
    FakeInstitutionRepository,
    make_donor,
    make_institution,
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
    assert repository.calls[0] == (DONOR_ID, RADIUS_KM)


def test_best_match_breaks_ties_by_id_whatever_the_row_order() -> None:
    first, second = make_institution(1), make_institution(2)
    repository = FakeInstitutionRepository([(second, 1), (first, 1)])

    results = BestMatchStrategy(repository).search(make_donor(), FILTERS, FIRST_PAGE)

    assert [result.institution for result in results] == [first, second]


def test_cause_text_passes_its_causes_and_name_to_the_repository() -> None:
    institution = make_institution(1, Cause.HEALTH)
    repository = FakeInstitutionRepository([(institution, 0.8)])

    results = CauseTextStrategy(repository).search(make_donor(), FILTERS, FIRST_PAGE)

    assert repository.calls == [(DONOR_ID, RADIUS_KM, FIRST_PAGE, (Cause.HEALTH,), "lar")]
    assert results == [SearchResult(institution, 0.8)]
