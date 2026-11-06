import pytest

from src.domain.charity import RegistryCode, RegistryData
from src.domain.enums import Verdict
from src.domain.exceptions import UnsupportedLegalNatureError
from src.models.institution import Association, Foundation, Institution, ReligiousOrganization
from src.models.user import Manager
from src.services.institution_factory import InstitutionFactory

SOCIAL_ASSISTANCE = RegistryCode("8800600", "Serviços de assistência social sem alojamento")
DATA = {"cnpj": "60979457000111", "legal_name": "ASSOCIACAO DE ASSISTENCIA A CRIANCA DEFICIENTE"}


def registry_data(code: str, description: str) -> RegistryData:
    return RegistryData("Ativa", RegistryCode(code, description), SOCIAL_ASSISTANCE)


@pytest.mark.parametrize(
    ("code", "description", "institution_class"),
    [
        ("3999", "Associação Privada", Association),
        ("399-9", "Associação Privada", Association),
        ("3069", "Fundação Privada", Foundation),
        ("3220", "Organização Religiosa", ReligiousOrganization),
    ],
)
def test_create_picks_the_institution_class_of_the_legal_nature(
    code: str, description: str, institution_class: type[Institution]
) -> None:
    manager = Manager()

    institution = InstitutionFactory.create(registry_data(code, description), manager, DATA)

    assert type(institution) is institution_class
    assert institution.manager is manager
    assert institution.cnpj == DATA["cnpj"]
    assert institution.legal_name == DATA["legal_name"]


def test_create_fills_the_verdict_and_the_reasons_of_the_classifier() -> None:
    registry = registry_data("3999", "Associação Privada")

    institution = InstitutionFactory.create(registry, Manager(), DATA)

    assert institution.verdict is Verdict.LIKELY_CHARITY
    assert institution.reasons == [
        "OK - Situação cadastral: Ativa",
        "OK - Natureza jurídica: 3999 - Associação Privada",
        "OK - Atividade principal: 8800600 - Serviços de assistência social sem alojamento",
    ]


def test_create_rejects_an_unsupported_legal_nature() -> None:
    registry = registry_data("2062", "Sociedade Empresária Limitada")
    manager = Manager()

    with pytest.raises(UnsupportedLegalNatureError, match="2062 - Sociedade Empresária Limitada"):
        InstitutionFactory.create(registry, manager, DATA)
