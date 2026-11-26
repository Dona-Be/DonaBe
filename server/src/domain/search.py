from dataclasses import dataclass

from src.domain.enums import Cause, Verdict

HIDDEN_VERDICTS = (Verdict.INACTIVE, Verdict.UNLIKELY)


@dataclass(frozen=True)
class SearchFilters:
    radius_km: float = 10
    causes: tuple[Cause, ...] = ()
    name: str | None = None


@dataclass(frozen=True)
class SearchPage:
    number: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (self.number - 1) * self.size
