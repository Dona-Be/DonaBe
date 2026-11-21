from typing import Annotated

from fastapi import APIRouter, Query, status

from src.api.authentication import CurrentManager, CurrentUserIfAny
from src.api.dependencies import NeedServiceDep
from src.api.parameters import DatabaseId
from src.domain.enums import NeedStatus
from src.models.need import Need
from src.schemas.need import NeedChanges, NewNeed, PublicNeed

router = APIRouter(tags=["needs"])


@router.post(
    "/institutions/{institution_id}/needs",
    status_code=status.HTTP_201_CREATED,
    response_model=PublicNeed,
    summary="Create a need for your institution",
)
def create_need(
    institution_id: DatabaseId,
    data: NewNeed,
    manager: CurrentManager,
    service: NeedServiceDep,
) -> Need:
    return service.create(manager, institution_id, data.model_dump())


@router.get(
    "/institutions/{institution_id}/needs",
    response_model=list[PublicNeed],
    summary="List an institution's needs",
)
def list_institution_needs(
    institution_id: DatabaseId,
    service: NeedServiceDep,
    user: CurrentUserIfAny,
    need_status: Annotated[NeedStatus | None, Query(alias="status")] = None,
) -> list[Need]:
    return service.list_by_institution(institution_id, user, need_status)


@router.patch(
    "/needs/{need_id}",
    response_model=PublicNeed,
    summary="Edit a need",
)
def update_need(
    need_id: DatabaseId,
    changes: NeedChanges,
    manager: CurrentManager,
    service: NeedServiceDep,
) -> Need:
    return service.update(manager, need_id, changes.model_dump(exclude_unset=True))


@router.post(
    "/needs/{need_id}/fulfill",
    response_model=PublicNeed,
    summary="Mark a need as fulfilled",
)
def fulfill_need(need_id: DatabaseId, manager: CurrentManager, service: NeedServiceDep) -> Need:
    return service.change_status(manager, need_id, NeedStatus.FULFILLED)


@router.post(
    "/needs/{need_id}/close",
    response_model=PublicNeed,
    summary="Close a need",
)
def close_need(need_id: DatabaseId, manager: CurrentManager, service: NeedServiceDep) -> Need:
    return service.change_status(manager, need_id, NeedStatus.CLOSED)
