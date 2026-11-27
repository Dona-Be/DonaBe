from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlalchemy import func, select
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

    @abstractmethod
    def count_open_by_institution(self, institution_ids: Sequence[int]) -> dict[int, int]:
        """Institutions without open needs are left out of the result."""


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

    def count_open_by_institution(self, institution_ids: Sequence[int]) -> dict[int, int]:
        if not institution_ids:
            return {}
        query = (
            select(Need.institution_id, func.count())
            .where(Need.institution_id.in_(institution_ids), Need.status == NeedStatus.OPEN)
            .group_by(Need.institution_id)
        )
        return dict(self._session.execute(query).tuples().all())
