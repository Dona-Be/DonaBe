from abc import ABC, abstractmethod

from geoalchemy2 import WKBElement
from psycopg.errors import UniqueViolation
from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.exceptions import InstitutionAlreadyExistsError
from src.domain.search import SEARCHABLE_VERDICTS, SearchFilters
from src.models.institution import METERS_PER_KM, Institution


def name_contains(text: str) -> ColumnElement[bool]:
    wanted = func.lower(func.unaccent(text))
    return or_(
        func.strpos(func.lower(func.unaccent(Institution.legal_name)), wanted) > 0,
        func.strpos(func.lower(func.unaccent(Institution.trade_name)), wanted) > 0,
    )


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
    def search(
        self, origin: WKBElement, filters: SearchFilters, *, limit: int | None, offset: int
    ) -> list[tuple[Institution, float]]: ...


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

    def search(
        self, origin: WKBElement, filters: SearchFilters, *, limit: int | None, offset: int
    ) -> list[tuple[Institution, float]]:
        distance_km = func.ST_Distance(Institution.location, origin) / METERS_PER_KM
        query = select(Institution, distance_km).where(
            Institution.verdict.in_(SEARCHABLE_VERDICTS), Institution.location.is_not(None)
        )
        if filters.max_distance_km is not None:
            radius = filters.max_distance_km * METERS_PER_KM
            query = query.where(func.ST_DWithin(Institution.location, origin, radius))
        if filters.causes:
            query = query.where(Institution.causes.overlap(filters.causes))
        if filters.text:
            query = query.where(name_contains(filters.text))
        nearest_first = query.order_by(distance_km, Institution.id).limit(limit).offset(offset)
        return list(self._session.execute(nearest_first).tuples())
