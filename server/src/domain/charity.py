from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from src.domain.enums import Verdict

ACTIVE_STATUS = "ativa"

# 3069 = Fundação Privada, 3999 = Associação Privada.
NONPROFIT_LEGAL_NATURES = frozenset({"3069", "3999"})

# CNAE prefixes: 8610/8690 health care, 87-88 social assistance, 9430 social rights advocacy.
CHARITY_CNAE_PREFIXES = ("8610", "8690", "87", "88", "9430")


@dataclass(frozen=True)
class RegistryCode:
    code: str
    description: str

    def __str__(self) -> str:
        return f"{self.code} - {self.description}"


@dataclass(frozen=True)
class RegistryData:
    registration_status: str
    legal_nature: RegistryCode
    main_activity: RegistryCode


@dataclass(frozen=True)
class CriterionResult:
    met: bool
    description: str
    observed_value: str

    @property
    def reason(self) -> str:
        marker = "OK" if self.met else "NÃO"
        return f"{marker} - {self.description}: {self.observed_value}"


class Criterion(ABC):
    description: ClassVar[str]

    def evaluate(self, data: RegistryData) -> CriterionResult:
        return CriterionResult(self.is_met(data), self.description, self.observed_value(data))

    @abstractmethod
    def is_met(self, data: RegistryData) -> bool: ...

    @abstractmethod
    def observed_value(self, data: RegistryData) -> str: ...


class ActiveRegistrationCriterion(Criterion):
    description = "Situação cadastral"

    def is_met(self, data: RegistryData) -> bool:
        return data.registration_status.strip().casefold() == ACTIVE_STATUS

    def observed_value(self, data: RegistryData) -> str:
        return data.registration_status


class NonprofitLegalNatureCriterion(Criterion):
    description = "Natureza jurídica"

    def is_met(self, data: RegistryData) -> bool:
        return data.legal_nature.code in NONPROFIT_LEGAL_NATURES

    def observed_value(self, data: RegistryData) -> str:
        return str(data.legal_nature)


class CharityActivityCriterion(Criterion):
    description = "Atividade principal"

    def is_met(self, data: RegistryData) -> bool:
        return data.main_activity.code.startswith(CHARITY_CNAE_PREFIXES)

    def observed_value(self, data: RegistryData) -> str:
        return str(data.main_activity)


@dataclass(frozen=True)
class Classification:
    verdict: Verdict
    reasons: tuple[str, ...]


def decide_verdict(active: bool, nonprofit: bool, charity_activity: bool) -> Verdict:
    if not active:
        return Verdict.INACTIVE
    if nonprofit and charity_activity:
        return Verdict.LIKELY_CHARITY
    if nonprofit:
        return Verdict.NONPROFIT
    return Verdict.UNLIKELY


class CharityClassifier:
    def __init__(self) -> None:
        self._active = ActiveRegistrationCriterion()
        self._nonprofit = NonprofitLegalNatureCriterion()
        self._charity_activity = CharityActivityCriterion()

    def classify(self, data: RegistryData) -> Classification:
        active = self._active.evaluate(data)
        nonprofit = self._nonprofit.evaluate(data)
        charity_activity = self._charity_activity.evaluate(data)
        verdict = decide_verdict(active.met, nonprofit.met, charity_activity.met)
        return Classification(verdict, (active.reason, nonprofit.reason, charity_activity.reason))
