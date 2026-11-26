from abc import ABC, abstractmethod
from collections.abc import Mapping

from src.domain.exceptions import InvalidSearchStrategyError
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

STRATEGY_NEAREST = "nearest"
STRATEGY_BEST_MATCH = "best_match"
STRATEGY_CAUSE_TEXT = "cause_text"


class SearchStrategy(ABC):
    def __init__(self, repository: InstitutionRepository) -> None:
        self._repository = repository

    @abstractmethod
    def search(
        self, donor: Donor, filters: SearchFilters, page: SearchPage
    ) -> list[Institution]: ...


class NearestStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[Institution]:
        rows = self._repository.list_within(donor.id, filters.radius_km, page)
        return [institution for institution, _ in rows]


class BestMatchStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[Institution]:
        rows = self._repository.list_within(donor.id, filters.radius_km, page=None)
        matches = [
            (
                self._score(institution, donor, distance_km),
                distance_km,
                institution.id,
                institution,
            )
            for institution, distance_km in rows
        ]
        matches.sort(key=lambda match: (-match[0], match[1], match[2]))
        return [match[3] for match in matches[page.offset : page.offset + page.size]]

    @staticmethod
    def _score(institution: Institution, donor: Donor, distance_km: float) -> int:
        proximity = ProximityDecorator(
            BaseMatchScore(),
            lambda _origin, _destination, km=distance_km: km,
        )
        match = VerifiedCnpjDecorator(PreferredCauseDecorator(proximity))
        return match.score(institution, donor)


class CauseTextStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[Institution]:
        rows = self._repository.list_within(
            donor.id, filters.radius_km, page, causes=filters.causes, name=filters.name
        )
        return [institution for institution, _ in rows]


class InstitutionSearchService:
    def __init__(self, repository: InstitutionRepository) -> None:
        self._strategies: Mapping[str, SearchStrategy] = {
            STRATEGY_NEAREST: NearestStrategy(repository),
            STRATEGY_BEST_MATCH: BestMatchStrategy(repository),
            STRATEGY_CAUSE_TEXT: CauseTextStrategy(repository),
        }

    def search(
        self,
        donor: Donor,
        strategy_name: str,
        filters: SearchFilters,
        page: SearchPage,
    ) -> list[Institution]:
        try:
            strategy = self._strategies[strategy_name]
        except KeyError as error:
            raise InvalidSearchStrategyError(strategy_name) from error
        return strategy.search(donor, filters, page)
