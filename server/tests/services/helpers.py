from geoalchemy2 import WKTElement
from sqlalchemy.orm import Session

from src.domain.enums import Cause
from src.domain.search import SearchFilters
from src.models.institution import WGS84_SRID
from src.models.user import Donor, Manager
from src.repositories.institutions import SqlAlchemyInstitutionRepository
from src.services.search_strategies import SearchResult, SearchStrategy
from tests.models.helpers import MANAGER_EMAIL, new_institution, profile

DONOR_LATITUDE = -23.55
DONOR_LONGITUDE = -46.63
DONOR_CAUSE = Cause.ELDERLY
# Kilometers in one degree of latitude near the donor, on the WGS84 ellipsoid
KM_PER_DEGREE = 110.75


def point_at(km_north: float) -> WKTElement:
    latitude = DONOR_LATITUDE + km_north / KM_PER_DEGREE
    return WKTElement(f"POINT({DONOR_LONGITUDE} {latitude})", srid=WGS84_SRID)


def at_km(name: str, km: float, **fields: object) -> dict[str, object]:
    return {"legal_name": name, "location": point_at(km), **fields}


def save_institutions(db_session: Session, *institutions: dict[str, object]) -> None:
    manager = Manager.from_profile(profile(MANAGER_EMAIL))
    for index, fields in enumerate(institutions):
        institution = new_institution(manager)
        institution.cnpj = f"{index:014d}"
        for field, value in fields.items():
            setattr(institution, field, value)
        db_session.add(institution)
    db_session.commit()


def search(
    db_session: Session, strategy: type[SearchStrategy], filters: SearchFilters, page: int = 1
) -> list[SearchResult]:
    donor = Donor(postal_code="01001000", location=point_at(0), preferred_causes=[DONOR_CAUSE])
    return strategy(SqlAlchemyInstitutionRepository(db_session)).search(donor, filters, page)


def names(results: list[SearchResult]) -> list[str]:
    return [result.institution.legal_name for result in results]
