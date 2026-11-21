from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.exceptions import UnknownSearchStrategyError
from src.domain.search import SearchFilters
from src.models.institution import Institution
from src.models.user import Donor
from src.repositories.institutions import InstitutionRepository
from src.services.match_score import (
    BaseMatchScore,
    PreferredCauseDecorator,
    ProximityDecorator,
    VerifiedCnpjDecorator,
)

PAGE_SIZE = 20


@dataclass(frozen=True)
class SearchResult:
    institution: Institution
    distance_km: float
    score: int | None = None
    reasons: tuple[str, ...] = ()


def offset_of(page: int) -> int:
    return (page - 1) * PAGE_SIZE


def radius_only(filters: SearchFilters) -> SearchFilters:
    return SearchFilters(max_distance_km=filters.max_distance_km)


def scored(institution: Institution, distance_km: float, donor: Donor) -> SearchResult:
    # The search already measured the distance, so no CEP is looked up again
    proximity = ProximityDecorator(BaseMatchScore(), lambda *_: distance_km)
    match = VerifiedCnpjDecorator(PreferredCauseDecorator(proximity))
    score = match.score(institution, donor)
    return SearchResult(institution, distance_km, score, tuple(match.reasons()))


class SearchStrategy(ABC):
    def __init__(self, repository: InstitutionRepository) -> None:
        self._repository = repository

    @abstractmethod
    def search(self, donor: Donor, filters: SearchFilters, page: int) -> list[SearchResult]: ...

    def _nearest_first(self, donor: Donor, filters: SearchFilters, page: int) -> list[SearchResult]:
        found = self._repository.search(
            donor.location, filters, limit=PAGE_SIZE, offset=offset_of(page)
        )
        return [SearchResult(institution, distance_km) for institution, distance_km in found]


class NearestStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: int) -> list[SearchResult]:
        return self._nearest_first(donor, radius_only(filters), page)


class BestMatchStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: int) -> list[SearchResult]:
        found = self._repository.search(donor.location, radius_only(filters), limit=None, offset=0)
        results = [scored(institution, distance_km, donor) for institution, distance_km in found]
        # The sort is stable, so equal scores stay nearest first
        results.sort(key=lambda result: result.score, reverse=True)
        start = offset_of(page)
        return results[start : start + PAGE_SIZE]


class CauseTextStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: int) -> list[SearchResult]:
        return self._nearest_first(donor, filters, page)


STRATEGY_CLASS_BY_NAME: dict[str, type[SearchStrategy]] = {
    "nearest": NearestStrategy,
    "best_match": BestMatchStrategy,
    "cause_text": CauseTextStrategy,
}


def strategy_named(name: str, repository: InstitutionRepository) -> SearchStrategy:
    strategy_class = STRATEGY_CLASS_BY_NAME.get(name)
    if strategy_class is None:
        raise UnknownSearchStrategyError(*STRATEGY_CLASS_BY_NAME)
    return strategy_class(repository)
