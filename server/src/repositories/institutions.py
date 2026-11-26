from abc import ABC, abstractmethod

from psycopg.errors import UniqueViolation
from sqlalchemy import func, or_, select
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
        donor_location = select(Donor.location).where(Donor.id == donor_id).scalar_subquery()
        distance_km = func.ST_Distance(Institution.location, donor_location) / METERS_PER_KM
        query = select(Institution, distance_km).where(
            Institution.verdict.not_in(HIDDEN_VERDICTS),
            Institution.location.is_not(None),
            func.ST_DWithin(Institution.location, donor_location, radius_km * METERS_PER_KM),
        )
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
