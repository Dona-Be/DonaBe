import pytest

from src.domain.enums import Cause, Verdict
from src.models.institution import Association, Institution
from src.models.user import Donor
from src.services.match_score import (
    BaseMatchScore,
    MatchScore,
    PreferredCauseDecorator,
    ProximityDecorator,
    VerifiedCnpjDecorator,
)

DONOR_CEP = "01001000"
INSTITUTION_CEP = "69945000"
ANIMALS_REASON = "Atende sua causa: Animais"
HEALTH_REASON = "Atende sua causa: Saúde"
NEAR_REASON = "Fica a até 2 km de você"
CHARITY_REASON = "CNPJ verificado: provável instituição beneficente"
NONPROFIT_REASON = "CNPJ verificado: entidade sem fins lucrativos"


class FakeDistance:
    def __init__(self, km: float) -> None:
        self.km = km
        self.calls: list[tuple[str, str]] = []

    def __call__(self, origin_cep: str, destination_cep: str) -> float:
        self.calls.append((origin_cep, destination_cep))
        return self.km


def institution(*causes: Cause, verdict: Verdict = Verdict.UNLIKELY) -> Institution:
    return Association(postal_code=INSTITUTION_CEP, causes=list(causes), verdict=verdict)


def donor(*preferred_causes: Cause, postal_code: str | None = DONOR_CEP) -> Donor:
    return Donor(postal_code=postal_code, preferred_causes=list(preferred_causes))


def all_decorators(km: float) -> MatchScore:
    proximity = ProximityDecorator(BaseMatchScore(), FakeDistance(km))
    return VerifiedCnpjDecorator(PreferredCauseDecorator(proximity))


def test_base_match_score_gives_the_base_score_without_reasons() -> None:
    match = BaseMatchScore()

    assert match.score(institution(), donor()) == 0
    assert match.reasons() == []


@pytest.mark.parametrize(
    ("km", "points", "reasons"),
    [
        (0.3, 30, [NEAR_REASON]),
        (2, 30, [NEAR_REASON]),
        (2.1, 20, ["Fica a até 5 km de você"]),
        (5, 20, ["Fica a até 5 km de você"]),
        (10, 10, ["Fica a até 10 km de você"]),
        (10.1, 0, []),
    ],
)
def test_proximity_adds_the_points_of_the_distance_band(
    km: float, points: int, reasons: list[str]
) -> None:
    match = ProximityDecorator(BaseMatchScore(), FakeDistance(km))

    assert match.score(institution(), donor()) == points
    assert match.reasons() == reasons


def test_proximity_measures_from_the_donor_cep_to_the_institution_cep() -> None:
    distance = FakeDistance(1)

    ProximityDecorator(BaseMatchScore(), distance).score(institution(), donor())

    assert distance.calls == [(DONOR_CEP, INSTITUTION_CEP)]


def test_proximity_skips_a_donor_without_cep() -> None:
    distance = FakeDistance(1)
    match = ProximityDecorator(BaseMatchScore(), distance)

    assert match.score(institution(), donor(postal_code=None)) == 0
    assert match.reasons() == []
    assert distance.calls == []


def test_preferred_cause_adds_points_and_a_reason_per_shared_cause() -> None:
    match = PreferredCauseDecorator(BaseMatchScore())
    shelter = institution(Cause.ANIMALS, Cause.ELDERLY, Cause.HEALTH)

    assert match.score(shelter, donor(Cause.HEALTH, Cause.ANIMALS, Cause.WOMEN)) == 30
    assert match.reasons() == [ANIMALS_REASON, HEALTH_REASON]


@pytest.mark.parametrize(
    ("verdict", "points", "reasons"),
    [
        (Verdict.LIKELY_CHARITY, 20, [CHARITY_REASON]),
        (Verdict.NONPROFIT, 10, [NONPROFIT_REASON]),
        (Verdict.INACTIVE, 0, []),
        (Verdict.UNLIKELY, 0, []),
    ],
)
def test_verified_cnpj_adds_the_points_of_the_verdict(
    verdict: Verdict, points: int, reasons: list[str]
) -> None:
    match = VerifiedCnpjDecorator(BaseMatchScore())

    assert match.score(institution(verdict=verdict), donor()) == points
    assert match.reasons() == reasons


def test_combined_decorators_add_their_points_and_reasons() -> None:
    match = all_decorators(km=1.5)
    shelter = institution(Cause.ANIMALS, verdict=Verdict.LIKELY_CHARITY)

    assert match.score(shelter, donor(Cause.ANIMALS)) == 65
    assert match.reasons() == [NEAR_REASON, ANIMALS_REASON, CHARITY_REASON]


def test_combined_decorators_keep_only_the_satisfied_criteria() -> None:
    match = all_decorators(km=40)
    clinic = institution(Cause.HEALTH, verdict=Verdict.NONPROFIT)

    assert match.score(clinic, donor(Cause.ANIMALS)) == 10
    assert match.reasons() == [NONPROFIT_REASON]


def test_reasons_follow_the_order_the_decorators_were_combined() -> None:
    match = PreferredCauseDecorator(VerifiedCnpjDecorator(BaseMatchScore()))
    shelter = institution(Cause.ANIMALS, verdict=Verdict.NONPROFIT)

    assert match.score(shelter, donor(Cause.ANIMALS)) == 25
    assert match.reasons() == [NONPROFIT_REASON, ANIMALS_REASON]


def test_reasons_describe_only_the_last_scored_institution() -> None:
    match = all_decorators(km=1.5)
    match.score(institution(Cause.ANIMALS, verdict=Verdict.LIKELY_CHARITY), donor(Cause.ANIMALS))

    match.score(institution(), donor(postal_code=None))

    assert match.reasons() == []
