from abc import ABC, abstractmethod
from collections.abc import Mapping

from sqlalchemy import func, or_, select
from sqlalchemy.sql import Select

from src.domain.exceptions import InvalidSearchStrategyError
from src.domain.search import HIDDEN_VERDICTS, SearchFilters, SearchPage
from src.models.institution import METERS_PER_KM, Institution
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

    def _base_query(self, donor: Donor, filters: SearchFilters) -> tuple[Select[tuple], object]:
        donor_location = select(Donor.location).where(Donor.id == donor.id).scalar_subquery()
        distance = func.ST_Distance(Institution.location, donor_location)
        query = select(Institution, distance.label("distance_meters")).where(
            Institution.verdict.not_in(HIDDEN_VERDICTS),
            Institution.location.is_not(None),
            func.ST_DWithin(
                Institution.location, donor_location, filters.radius_km * METERS_PER_KM
            ),
        )
        return query, distance


class NearestStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[Institution]:
        query, distance = self._base_query(donor, filters)
        rows = self._repository.search(query.order_by(distance, Institution.id), page)
        return [row[0] for row in rows]


class BestMatchStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[Institution]:
        query, _ = self._base_query(donor, filters)
        rows = self._repository.search(query)
        matches = [
            (
                self._score(institution, donor, distance_meters),
                distance_meters,
                institution.id,
                institution,
            )
            for institution, distance_meters in rows
        ]
        matches.sort(key=lambda match: (-match[0], match[1], match[2]))
        return [match[3] for match in matches[page.offset : page.offset + page.size]]

    @staticmethod
    def _score(institution: Institution, donor: Donor, distance_meters: float) -> int:
        distance_km = float(distance_meters) / METERS_PER_KM
        proximity = ProximityDecorator(
            BaseMatchScore(),
            lambda _origin, _destination, km=distance_km: km,
        )
        match = VerifiedCnpjDecorator(PreferredCauseDecorator(proximity))
        return match.score(institution, donor)


class CauseTextStrategy(SearchStrategy):
    def search(self, donor: Donor, filters: SearchFilters, page: SearchPage) -> list[Institution]:
        query, distance = self._base_query(donor, filters)
        if filters.causes:
            query = query.where(Institution.causes.overlap(list(filters.causes)))
        if filters.name and filters.name.strip():
            # strpos, not LIKE: unaccent can map fullwidth signs to % and _
            term = func.lower(func.unaccent(filters.name.strip()))
            legal_name = func.lower(func.unaccent(Institution.legal_name))
            trade_name = func.lower(func.unaccent(Institution.trade_name))
            query = query.where(
                or_(func.strpos(legal_name, term) > 0, func.strpos(trade_name, term) > 0)
            )
        rows = self._repository.search(query.order_by(distance, Institution.id), page)
        return [row[0] for row in rows]


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
