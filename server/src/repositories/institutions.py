from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from psycopg.errors import UniqueViolation
from sqlalchemy import ColumnElement, Row, and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.enums import Cause
from src.domain.exceptions import InstitutionAlreadyExistsError
from src.domain.search import HIDDEN_VERDICTS, SearchPage
from src.models.institution import METERS_PER_KM, Institution
from src.models.user import Donor


class InstitutionRepository(ABC):
    @abstractmethod
    def save(self, institution: Institution) -> None: ...

    @abstractmethod
    def find_by_id(self, institution_id: int) -> Institution | None: ...

    @abstractmethod
    def find_by_cnpj(self, cnpj: str) -> Institution | None: ...

    @abstractmethod
    def list_by_manager(self, manager_id: int) -> list[Institution]: ...

    @abstractmethod
    def list_within(
        self,
        donor_id: int,
        radius_km: float,
        page: SearchPage | None,
        *,
        causes: tuple[Cause, ...] = (),
        name: str | None = None,
    ) -> list[tuple[Institution, float]]: ...

    @abstractmethod
    def list_match_candidates(self, donor_id: int, radius_km: float) -> Iterator[Row[Any]]: ...

    @abstractmethod
    def find_by_ids(self, institution_ids: list[int]) -> dict[int, Institution]: ...


class SqlAlchemyInstitutionRepository(InstitutionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, institution: Institution) -> None:
        self._session.add(institution)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if not isinstance(error.orig, UniqueViolation):
                raise
            raise InstitutionAlreadyExistsError(institution.cnpj) from error

    def find_by_id(self, institution_id: int) -> Institution | None:
        return self._session.get(Institution, institution_id)

    def find_by_cnpj(self, cnpj: str) -> Institution | None:
        return self._session.scalar(select(Institution).where(Institution.cnpj == cnpj))

    def list_by_manager(self, manager_id: int) -> list[Institution]:
        own = select(Institution).where(Institution.manager_id == manager_id)
        return list(self._session.scalars(own.order_by(Institution.id)))

    def list_within(
        self,
        donor_id: int,
        radius_km: float,
        page: SearchPage | None,
        *,
        causes: tuple[Cause, ...] = (),
        name: str | None = None,
    ) -> list[tuple[Institution, float]]:
        distance_km, visible = self._visible_within(donor_id, radius_km)
        query = select(Institution, distance_km).where(visible)
        if causes:
            query = query.where(Institution.causes.overlap(list(causes)))
        if name and name.strip():
            # strpos, not LIKE: unaccent can map fullwidth signs to % and _
            term = func.lower(func.unaccent(name.strip()))
            legal_name = func.lower(func.unaccent(Institution.legal_name))
            trade_name = func.lower(func.unaccent(Institution.trade_name))
            query = query.where(
                or_(func.strpos(legal_name, term) > 0, func.strpos(trade_name, term) > 0)
            )
        query = query.order_by(distance_km, Institution.id)
        if page is not None:
            query = query.limit(page.size).offset(page.offset)
        return list(self._session.execute(query).tuples())

    def list_match_candidates(self, donor_id: int, radius_km: float) -> Iterator[Row[Any]]:
        distance_km, visible = self._visible_within(donor_id, radius_km)
        query = select(
            Institution.id,
            Institution.causes,
            Institution.verdict,
            Institution.postal_code,
            distance_km.label("distance_km"),
        ).where(visible)
        # Streamed in batches, so not every row is in memory at once
        return self._session.execute(query.execution_options(yield_per=1000))

    def find_by_ids(self, institution_ids: list[int]) -> dict[int, Institution]:
        query = select(Institution).where(Institution.id.in_(institution_ids))
        return {institution.id: institution for institution in self._session.scalars(query)}

    @staticmethod
    def _visible_within(
        donor_id: int, radius_km: float
    ) -> tuple[ColumnElement[Any], ColumnElement[bool]]:
        donor_location = select(Donor.location).where(Donor.id == donor_id).scalar_subquery()
        distance_km = func.ST_Distance(Institution.location, donor_location) / METERS_PER_KM
        visible = and_(
            Institution.verdict.not_in(HIDDEN_VERDICTS),
            Institution.location.is_not(None),
            func.ST_DWithin(Institution.location, donor_location, radius_km * METERS_PER_KM),
        )
        return distance_km, visible
