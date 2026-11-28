from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

from src.domain.enums import Cause, Verdict
from src.domain.search import SearchFilters, SearchPage
from src.models.user import Donor
from tests.models.helpers import point_at

DONOR_ID = 12
RADIUS_KM = 8
FIRST_PAGE = SearchPage()
FILTERS = SearchFilters(radius_km=RADIUS_KM, causes=(Cause.HEALTH,), name="lar")


class FakeInstitutionRepository:
    def __init__(self, rows: list[tuple[Any, float]] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[tuple[Any, ...]] = []

    def list_within(
        self,
        donor_id: int,
        radius_km: float,
        page: SearchPage | None,
        *,
        causes: tuple[Cause, ...] = (),
        name: str | None = None,
    ) -> list[tuple[Any, float]]:
        self.calls.append((donor_id, radius_km, page, causes, name))
        if page is None:
            return self.rows
        return self.rows[page.offset : page.offset + page.size]

    def list_match_candidates(self, donor_id: int, radius_km: float) -> Iterator[SimpleNamespace]:
        self.calls.append((donor_id, radius_km))
        return iter([SimpleNamespace(**vars(row), distance_km=km) for row, km in self.rows])

    def find_by_ids(self, institution_ids: list[int]) -> dict[int, Any]:
        return {row.id: row for row, _ in self.rows if row.id in institution_ids}


class FakeNeedRepository:
    def __init__(self, open_needs: dict[int, int] | None = None) -> None:
        self.open_needs = open_needs or {}
        self.calls: list[list[int]] = []

    def count_open_by_institution(self, institution_ids: list[int]) -> dict[int, int]:
        self.calls.append(list(institution_ids))
        return {key: value for key, value in self.open_needs.items() if key in institution_ids}


def make_donor(*causes: Cause) -> Donor:
    return Donor(
        id=DONOR_ID,
        postal_code="01310200",
        location=point_at(0),
        preferred_causes=list(causes),
    )


def make_institution(
    institution_id: int,
    *causes: Cause,
    verdict: Verdict = Verdict.LIKELY_CHARITY,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=institution_id,
        causes=list(causes),
        verdict=verdict,
        postal_code="01310200",
    )
