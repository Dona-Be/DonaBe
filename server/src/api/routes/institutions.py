from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.api.authentication import CurrentDonor, CurrentManager, get_current_manager
from src.api.dependencies import InstitutionSearchServiceDep, InstitutionServiceDep
from src.api.parameters import MAX_INTEGER, DatabaseId
from src.api.rate_limits import limit_cep_lookups, limit_cnpj_lookups
from src.domain.enums import SearchStrategyName
from src.domain.search import (
    DEFAULT_SEARCH_RADIUS_KM,
    MAX_SEARCH_RADIUS_KM,
    SearchFilters,
    SearchPage,
)
from src.models.institution import Institution
from src.schemas.institution import (
    InstitutionChanges,
    InstitutionPage,
    InstitutionPreview,
    InstitutionSearchResult,
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


# Declared before /{institution_id}, or "search" would be read as an id.
@router.get(
    "/search",
    summary="Search the institutions near you",
    description=(
        "20 per page, within max_distance_km of your location. nearest orders by distance; "
        "best_match orders by score and explains it in match_reasons; cause_text orders by "
        "distance. score is null and match_reasons is empty outside best_match."
    ),
)
def search_institutions(
    donor: CurrentDonor,
    service: InstitutionSearchServiceDep,
    strategy: SearchStrategyName = SearchStrategyName.NEAREST,
    max_distance_km: Annotated[
        float, Query(gt=0, le=MAX_SEARCH_RADIUS_KM)
    ] = DEFAULT_SEARCH_RADIUS_KM,
    page: Annotated[int, Query(ge=1, le=MAX_INTEGER)] = 1,
) -> list[InstitutionSearchResult]:
    filters = SearchFilters(radius_km=max_distance_km)
    results = service.search(donor, strategy, filters, SearchPage(page))
    return [InstitutionSearchResult.from_result(result) for result in results]


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
