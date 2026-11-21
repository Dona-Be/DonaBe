from dataclasses import dataclass

from src.domain.enums import Cause, Verdict

SEARCHABLE_VERDICTS = (Verdict.LIKELY_CHARITY, Verdict.NONPROFIT)


@dataclass(frozen=True)
class SearchFilters:
    max_distance_km: float | None = None
    causes: tuple[Cause, ...] = ()
    text: str | None = None
