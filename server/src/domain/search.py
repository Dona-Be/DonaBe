from dataclasses import dataclass

from src.domain.enums import Cause, Verdict

HIDDEN_VERDICTS = (Verdict.INACTIVE, Verdict.UNLIKELY)
DEFAULT_SEARCH_RADIUS_KM = 10
# best_match scores every institution in the radius, so a larger radius must be measured first.
MAX_SEARCH_RADIUS_KM = 20


@dataclass(frozen=True)
class SearchFilters:
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM
    causes: tuple[Cause, ...] = ()
    name: str | None = None


@dataclass(frozen=True)
class SearchPage:
    number: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (self.number - 1) * self.size
