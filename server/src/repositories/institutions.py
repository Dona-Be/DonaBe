from abc import ABC, abstractmethod
from typing import Any

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.engine import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from src.domain.exceptions import InstitutionAlreadyExistsError
from src.domain.search import SearchPage
from src.models.institution import Institution


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
    def search(self, query: Select[Any], page: SearchPage | None = None) -> list[Row[Any]]: ...


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

    def search(self, query: Select[Any], page: SearchPage | None = None) -> list[Row[Any]]:
        if page is not None:
            query = query.limit(page.size).offset(page.offset)
        return list(self._session.execute(query))
