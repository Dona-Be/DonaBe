from datetime import UTC, datetime
from typing import Any

from src.domain.enums import NeedStatus
from src.domain.exceptions import (
    InstitutionNotFoundError,
    NeedNotFoundError,
    NeedNotOpenError,
    NotNeedManagerError,
)
from src.models.institution import Institution
from src.models.need import Need
from src.models.user import Manager, User
from src.repositories.institutions import InstitutionRepository
from src.repositories.needs import NeedRepository


class NeedService:
    def __init__(self, repository: NeedRepository, institutions: InstitutionRepository) -> None:
        self._repository = repository
        self._institutions = institutions

    def create(self, manager: Manager, institution_id: int, data: dict[str, Any]) -> Need:
        institution = self._find_institution(institution_id)
        if institution.manager_id != manager.id:
            raise NotNeedManagerError()
        need = Need(institution=institution, status=NeedStatus.OPEN, **data)
        self._repository.save(need)
        return need

    def update(self, manager: Manager, need_id: int, changes: dict[str, Any]) -> Need:
        need = self._find_need(need_id)
        self._check_owner(manager, need)
        for field, value in changes.items():
            if value is None and field != "quantity":
                continue
            setattr(need, field, value)
        self._repository.save(need)
        return need

    def change_status(self, manager: Manager, need_id: int, new_status: NeedStatus) -> Need:
        need = self._find_need(need_id)
        self._check_owner(manager, need)
        if need.status is not NeedStatus.OPEN:
            raise NeedNotOpenError()
        need.status = new_status
        need.closed_at = datetime.now(UTC)
        self._repository.save(need)
        return need

    def list_by_institution(
        self, institution_id: int, user: User | None, status: NeedStatus | None
    ) -> list[Need]:
        institution = self._find_institution(institution_id)
        is_owner = isinstance(user, Manager) and institution.manager_id == user.id
        if is_owner:
            return self._repository.list_by_institution(institution_id, status)
        if status is not None and status is not NeedStatus.OPEN:
            return []
        return self._repository.list_by_institution(institution_id, NeedStatus.OPEN)

    def _find_institution(self, institution_id: int) -> Institution:
        institution = self._institutions.find_by_id(institution_id)
        if institution is None:
            raise InstitutionNotFoundError()
        return institution

    def _find_need(self, need_id: int) -> Need:
        need = self._repository.find_by_id(need_id)
        if need is None:
            raise NeedNotFoundError()
        return need

    def _check_owner(self, manager: Manager, need: Need) -> None:
        institution = self._find_institution(need.institution_id)
        if institution.manager_id != manager.id:
            raise NotNeedManagerError()
