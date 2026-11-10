from collections.abc import Mapping
from typing import Any

from src.domain.charity import CharityClassifier, RegistryData, digits_only
from src.domain.exceptions import UnsupportedLegalNatureError
from src.models.institution import Association, Foundation, Institution, ReligiousOrganization
from src.models.user import Manager

INSTITUTION_CLASS_BY_LEGAL_NATURE: dict[str, type[Institution]] = {
    "3999": Association,
    "3069": Foundation,
    "3220": ReligiousOrganization,
}


class InstitutionFactory:
    @staticmethod
    def create(
        registry_data: RegistryData, manager: Manager, data: Mapping[str, Any]
    ) -> Institution:
        legal_nature = registry_data.legal_nature
        institution_class = INSTITUTION_CLASS_BY_LEGAL_NATURE.get(digits_only(legal_nature.code))
        if institution_class is None:
            raise UnsupportedLegalNatureError(str(legal_nature))
        classification = CharityClassifier().classify(registry_data)
        return institution_class(
            **data,
            manager=manager,
            verdict=classification.verdict,
            reasons=list(classification.reasons),
        )
