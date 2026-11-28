from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.api.authentication import CurrentDonor, CurrentManager, get_current_manager
from src.api.dependencies import InstitutionSearchServiceDep, InstitutionServiceDep
from src.api.parameters import DatabaseId
from src.api.rate_limits import limit_cep_lookups, limit_cnpj_lookups
from src.domain.search import SearchPage
from src.models.institution import Institution
from src.schemas.institution import (
    InstitutionChanges,
    InstitutionPage,
    InstitutionPreview,
    InstitutionSearch,
    InstitutionSearchResult,
    NewInstitution,
    PublicInstitution,
)
from src.services.search_strategies import SearchResult

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


def search_response(result: SearchResult) -> InstitutionSearchResult:
    institution = result.institution
    return InstitutionSearchResult(
        id=institution.id,
        type=institution.type,
        legal_name=institution.legal_name,
        trade_name=institution.trade_name,
        causes=institution.causes,
        verdict=institution.verdict,
        distance_km=result.distance_km,
        score=result.score,
        match_reasons=list(result.reasons),
        open_needs_count=result.open_needs_count,
    )


# Declared before /{institution_id}, or "search" would be read as an id.
@router.get(
    "/search",
    summary="Search the institutions near you",
    description="20 per page. Only best_match scores, and only cause_text uses causes and q.",
)
def search_institutions(
    donor: CurrentDonor,
    service: InstitutionSearchServiceDep,
    search: Annotated[InstitutionSearch, Query()],
) -> list[InstitutionSearchResult]:
    results = service.search(donor, search.strategy, search.filters(), SearchPage(search.page))
    return [search_response(result) for result in results]


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
