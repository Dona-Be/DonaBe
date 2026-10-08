import pytest

from src.domain.charity import (
    CharityActivityCriterion,
    CharityClassifier,
    RegistryCode,
    RegistryData,
)
from src.domain.enums import Verdict

PRIVATE_ASSOCIATION = RegistryCode("3999", "Associação Privada")
PRIVATE_FOUNDATION = RegistryCode("3069", "Fundação Privada")
LIMITED_COMPANY = RegistryCode("2062", "Sociedade Empresária Limitada")
SOCIAL_ASSISTANCE = RegistryCode("8800600", "Serviços de assistência social sem alojamento")
HOSPITAL_CARE = RegistryCode("8610101", "Atividades de atendimento hospitalar")
RELIGIOUS_ORGANIZATION = RegistryCode("9491000", "Atividades de organizações religiosas")
IT_CONSULTING = RegistryCode("6204000", "Consultoria em tecnologia da informação")


def registry_data(
    status: str = "Ativa",
    legal_nature: RegistryCode = PRIVATE_ASSOCIATION,
    main_activity: RegistryCode = SOCIAL_ASSISTANCE,
) -> RegistryData:
    return RegistryData(status, legal_nature, main_activity)


@pytest.mark.parametrize(
    ("status", "legal_nature", "main_activity", "verdict"),
    [
        ("Ativa", PRIVATE_ASSOCIATION, SOCIAL_ASSISTANCE, Verdict.LIKELY_CHARITY),
        ("ATIVA ", PRIVATE_FOUNDATION, HOSPITAL_CARE, Verdict.LIKELY_CHARITY),
        ("Ativa", PRIVATE_FOUNDATION, RELIGIOUS_ORGANIZATION, Verdict.NONPROFIT),
        ("Ativa", LIMITED_COMPANY, SOCIAL_ASSISTANCE, Verdict.UNLIKELY),
        ("Ativa", LIMITED_COMPANY, IT_CONSULTING, Verdict.UNLIKELY),
        ("Baixada", PRIVATE_ASSOCIATION, SOCIAL_ASSISTANCE, Verdict.INACTIVE),
        ("Inapta", LIMITED_COMPANY, IT_CONSULTING, Verdict.INACTIVE),
    ],
)
def test_classifies_by_status_legal_nature_and_activity(
    status: str, legal_nature: RegistryCode, main_activity: RegistryCode, verdict: Verdict
) -> None:
    data = registry_data(status, legal_nature, main_activity)

    assert CharityClassifier().classify(data).verdict is verdict


def test_gives_one_readable_reason_per_criterion() -> None:
    data = registry_data(main_activity=IT_CONSULTING)

    assert CharityClassifier().classify(data).reasons == (
        "OK - Situação cadastral: Ativa",
        "OK - Natureza jurídica: 3999 - Associação Privada",
        "NÃO - Atividade principal: 6204000 - Consultoria em tecnologia da informação",
    )


def test_marks_every_failed_criterion() -> None:
    data = registry_data("Baixada", LIMITED_COMPANY, IT_CONSULTING)

    assert all(reason.startswith("NÃO - ") for reason in CharityClassifier().classify(data).reasons)


@pytest.mark.parametrize(
    ("cnae", "is_charity"),
    [
        ("8610101", True),
        ("8690901", True),
        ("8711501", True),
        ("8800600", True),
        ("9430800", True),
        ("6204000", False),
    ],
)
def test_charity_activity_matches_the_cnae_prefixes(cnae: str, is_charity: bool) -> None:
    data = registry_data(main_activity=RegistryCode(cnae, "Atividade"))

    assert CharityActivityCriterion().is_met(data) is is_charity
