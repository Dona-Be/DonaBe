from fastapi import APIRouter, Depends, status

from src.api.authentication import CurrentManager, get_current_manager
from src.api.dependencies import InstitutionServiceDep
from src.api.parameters import DatabaseId
from src.api.rate_limits import limit_cep_lookups, limit_cnpj_lookups
from src.models.institution import Institution
from src.schemas.institution import (
    InstitutionChanges,
    InstitutionPage,
    InstitutionPreview,
    NewInstitution,
    PublicInstitution,
)

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get(
    "/lookup",
    response_model=InstitutionPreview,
    summary="Preview the institution of a CNPJ",
    description="Refuses the same CNPJs as the registration, saving nothing.",
    dependencies=[Depends(limit_cnpj_lookups)],
)
def preview_institution(
    cnpj: str, manager: CurrentManager, service: InstitutionServiceDep
) -> Institution:
    return service.preview(manager, cnpj)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PublicInstitution,
    summary="Register an institution",
    description="Fields left out or null come from the official CNPJ data.",
    dependencies=[Depends(limit_cnpj_lookups), Depends(limit_cep_lookups)],
)
def create_institution(
    data: NewInstitution, manager: CurrentManager, service: InstitutionServiceDep
) -> Institution:
    details = data.model_dump(exclude_none=True, exclude={"cnpj"})
    return service.create(manager, data.cnpj, details)


@router.get("/me", response_model=list[PublicInstitution], summary="List your institutions")
def list_my_institutions(
    manager: CurrentManager, service: InstitutionServiceDep
) -> list[Institution]:
    return service.list_of(manager)


@router.get(
    "/{institution_id}",
    response_model=InstitutionPage,
    summary="Read the public page of an institution",
)
def read_institution(institution_id: DatabaseId, service: InstitutionServiceDep) -> Institution:
    return service.find(institution_id)


@router.patch(
    "/{institution_id}",
    response_model=PublicInstitution,
    summary="Edit your institution",
    description="Fields left out or null are kept. An empty text removes an optional field.",
    # The manager is checked first, so the limiter cannot replace its 401.
    dependencies=[Depends(get_current_manager), Depends(limit_cep_lookups)],
)
def update_institution(
    institution_id: DatabaseId,
    changes: InstitutionChanges,
    manager: CurrentManager,
    service: InstitutionServiceDep,
) -> Institution:
    return service.update(manager, institution_id, changes.model_dump(exclude_none=True))
