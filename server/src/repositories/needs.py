from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.enums import NeedStatus
from src.models.need import Need


class NeedRepository(ABC):
    @abstractmethod
    def save(self, need: Need) -> None: ...

    @abstractmethod
    def find_by_id(self, need_id: int) -> Need | None: ...

    @abstractmethod
    def list_by_institution(self, institution_id: int, status: NeedStatus | None) -> list[Need]: ...


class SqlAlchemyNeedRepository(NeedRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, need: Need) -> None:
        self._session.add(need)
        self._session.commit()

    def find_by_id(self, need_id: int) -> Need | None:
        return self._session.get(Need, need_id)

    def list_by_institution(self, institution_id: int, status: NeedStatus | None) -> list[Need]:
        query = select(Need).where(Need.institution_id == institution_id)
        if status is not None:
            query = query.where(Need.status == status)
        return list(self._session.scalars(query.order_by(Need.id)))
