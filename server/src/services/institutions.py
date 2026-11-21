from typing import Any

from src.connectors.schemas import Company
from src.domain.cep import normalize_cep
from src.domain.cnpj import normalize_cnpj
from src.domain.enums import Verdict
from src.domain.exceptions import (
    InactiveCnpjError,
    IncompleteAddressError,
    InstitutionAlreadyExistsError,
    InstitutionNotFoundError,
    NotInstitutionManagerError,
)
from src.models.institution import Institution
from src.models.user import Manager
from src.repositories.institutions import InstitutionRepository
from src.services.cnpj import CnpjService
from src.services.institution_factory import InstitutionFactory
from src.services.locations import LocationService

REQUIRED_ADDRESS_FIELDS = ("street", "number", "neighborhood", "postal_code")


def official_data(company: Company) -> dict[str, Any]:
    return {
        "cnpj": company.tax_id,
        "legal_name": company.legal_name,
        "trade_name": company.trade_name,
        "cnpj_data": company.raw_data,
        **company.address.model_dump(exclude={"coordinates"}),
    }


class InstitutionService:
    def __init__(
        self, repository: InstitutionRepository, cnpj: CnpjService, locations: LocationService
    ) -> None:
        self._repository = repository
        self._cnpj = cnpj
        self._locations = locations

    def preview(self, manager: Manager, cnpj: str) -> Institution:
        return self._build(manager, cnpj, {})

    def create(self, manager: Manager, cnpj: str, details: dict[str, Any]) -> Institution:
        institution = self._build(manager, cnpj, details)
        if any(getattr(institution, field) is None for field in REQUIRED_ADDRESS_FIELDS):
            raise IncompleteAddressError()
        institution.location = self._locations.point_of(institution.postal_code)
        self._repository.save(institution)
        return institution

    def list_of(self, manager: Manager) -> list[Institution]:
        return self._repository.list_by_manager(manager.id)

    def find(self, institution_id: int) -> Institution:
        institution = self._repository.find_by_id(institution_id)
        if institution is None:
            raise InstitutionNotFoundError()
        return institution

    def update(self, manager: Manager, institution_id: int, changes: dict[str, Any]) -> Institution:
        institution = self.find(institution_id)
        if institution.manager_id != manager.id:
            raise NotInstitutionManagerError()
        for field, value in changes.items():
            if field == "postal_code" and normalize_cep(value) != institution.postal_code:
                institution.location = self._locations.point_of(value)
            setattr(institution, field, value)
        self._repository.save(institution)
        return institution

    def _build(self, manager: Manager, cnpj: str, details: dict[str, Any]) -> Institution:
        tax_id = normalize_cnpj(cnpj)
        if self._repository.find_by_cnpj(tax_id) is not None:
            raise InstitutionAlreadyExistsError(tax_id)
        classified = self._cnpj.classify(tax_id)
        if classified.classification.verdict is Verdict.INACTIVE:
            raise InactiveCnpjError()
        company = classified.company
        data = {**official_data(company), **details}
        return InstitutionFactory.create(company.registry_data(), manager, data)
