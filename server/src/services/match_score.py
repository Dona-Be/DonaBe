from abc import ABC, abstractmethod
from collections.abc import Callable

from src.domain.enums import Cause, Verdict
from src.models.institution import Institution
from src.models.user import Donor

BASE_SCORE = 0
# Each band is (maximum distance in km, points), nearest band first.
PROXIMITY_BANDS = ((2, 30), (5, 20), (10, 10))
PREFERRED_CAUSE_POINTS = 15
VERDICT_POINTS = {Verdict.LIKELY_CHARITY: 20, Verdict.NONPROFIT: 10}

CAUSE_LABELS = {
    Cause.CHILDREN_AND_TEENAGERS: "Crianças e adolescentes",
    Cause.ELDERLY: "Idosos",
    Cause.PEOPLE_WITH_DISABILITIES: "Pessoas com deficiência",
    Cause.HEALTH: "Saúde",
    Cause.EDUCATION: "Educação",
    Cause.HUNGER_RELIEF: "Combate à fome",
    Cause.HOMELESS_PEOPLE: "Pessoas em situação de rua",
    Cause.WOMEN: "Mulheres",
    Cause.ANIMALS: "Animais",
    Cause.ENVIRONMENT: "Meio ambiente",
}
VERDICT_LABELS = {
    Verdict.LIKELY_CHARITY: "provável instituição beneficente",
    Verdict.NONPROFIT: "entidade sem fins lucrativos",
}

Bonus = tuple[int, str]


class MatchScore(ABC):
    @abstractmethod
    def score(self, institution: Institution, donor: Donor) -> int: ...

    @abstractmethod
    def reasons(self) -> list[str]: ...


class BaseMatchScore(MatchScore):
    def score(self, institution: Institution, donor: Donor) -> int:
        return BASE_SCORE

    def reasons(self) -> list[str]:
        return []


class MatchScoreDecorator(MatchScore):
    def __init__(self, inner: MatchScore) -> None:
        self._inner = inner
        self._last_bonuses: list[Bonus] = []

    def score(self, institution: Institution, donor: Donor) -> int:
        self._last_bonuses = self.bonuses(institution, donor)
        own_points = sum(points for points, _ in self._last_bonuses)
        return self._inner.score(institution, donor) + own_points

    def reasons(self) -> list[str]:
        return self._inner.reasons() + [reason for _, reason in self._last_bonuses]

    @abstractmethod
    def bonuses(self, institution: Institution, donor: Donor) -> list[Bonus]: ...


class ProximityDecorator(MatchScoreDecorator):
    def __init__(self, inner: MatchScore, distance_km: Callable[[str, str], float]) -> None:
        super().__init__(inner)
        self._distance_km = distance_km

    def bonuses(self, institution: Institution, donor: Donor) -> list[Bonus]:
        if donor.postal_code is None:
            return []
        distance = self._distance_km(donor.postal_code, institution.postal_code)
        for max_km, points in PROXIMITY_BANDS:
            if distance <= max_km:
                return [(points, f"Fica a até {max_km} km de você")]
        return []


class PreferredCauseDecorator(MatchScoreDecorator):
    def bonuses(self, institution: Institution, donor: Donor) -> list[Bonus]:
        return [
            (PREFERRED_CAUSE_POINTS, f"Atende sua causa: {CAUSE_LABELS[cause]}")
            for cause in institution.causes
            if cause in donor.preferred_causes
        ]


class VerifiedCnpjDecorator(MatchScoreDecorator):
    def bonuses(self, institution: Institution, donor: Donor) -> list[Bonus]:
        verdict = institution.verdict
        if verdict not in VERDICT_POINTS:
            return []
        return [(VERDICT_POINTS[verdict], f"CNPJ verificado: {VERDICT_LABELS[verdict]}")]
