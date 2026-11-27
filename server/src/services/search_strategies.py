from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass

from src.domain.enums import SearchStrategyName
from src.domain.exceptions import DonorWithoutLocationError, InvalidSearchStrategyError
from src.domain.search import SearchFilters, SearchPage
from src.models.institution import Institution
from src.models.user import Donor
from src.repositories.institutions import InstitutionRepository
from src.services.match_score import (
    BaseMatchScore,
    PreferredCauseDecorator,
    ProximityDecorator,
    VerifiedCnpjDecorator,
)


@dataclass(frozen=True)
class SearchResult:
    institution: Institution
    distance_km: float
    score: int | None = None
    reasons: tuple[str, ...] = ()


class SearchStrategy(ABC):
    def __init__(self, repository: InstitutionRepository) -> None:
        self._repository = repository

    @abstractmethod
    def search(
        self, donor: Donor, filters: SearchFilters, page: SearchPage
    ) -> list[SearchResult]: ...


class NearestStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[SearchResult]:
        rows = self._repository.list_within(donor.id, filters.radius_km, page)
        return [SearchResult(institution, distance_km) for institution, distance_km in rows]


class BestMatchStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[SearchResult]:
        rows = self._repository.list_within(donor.id, filters.radius_km, page=None)
        matches = [
            self._scored(institution, donor, distance_km) for institution, distance_km in rows
        ]
        matches.sort(key=lambda match: (-match.score, match.distance_km, match.institution.id))
        return matches[page.offset : page.offset + page.size]

    @staticmethod
    def _scored(institution: Institution, donor: Donor, distance_km: float) -> SearchResult:
        proximity = ProximityDecorator(
            BaseMatchScore(),
            lambda _origin, _destination, km=distance_km: km,
        )
        match = VerifiedCnpjDecorator(PreferredCauseDecorator(proximity))
        score = match.score(institution, donor)
        return SearchResult(institution, distance_km, score, tuple(match.reasons()))


class CauseTextStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[SearchResult]:
        rows = self._repository.list_within(
            donor.id, filters.radius_km, page, causes=filters.causes, name=filters.name
        )
        return [SearchResult(institution, distance_km) for institution, distance_km in rows]


class InstitutionSearchService:
    def __init__(self, repository: InstitutionRepository) -> None:
        self._strategies: Mapping[str, SearchStrategy] = {
            SearchStrategyName.NEAREST: NearestStrategy(repository),
            SearchStrategyName.BEST_MATCH: BestMatchStrategy(repository),
            SearchStrategyName.CAUSE_TEXT: CauseTextStrategy(repository),
        }

    def search(
        self,
        donor: Donor,
        strategy_name: str,
        filters: SearchFilters,
        page: SearchPage,
    ) -> list[SearchResult]:
        try:
            strategy = self._strategies[strategy_name]
        except KeyError as error:
            raise InvalidSearchStrategyError(strategy_name) from error
        # Without a location the radius has no center, and the search would come back empty.
        if donor.location is None:
            raise DonorWithoutLocationError
        return strategy.search(donor, filters, page)
