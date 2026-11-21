import pytest
from sqlalchemy.orm import Session

from src.domain.enums import Cause
from src.domain.search import SearchFilters
from src.services.search_strategies import CauseTextStrategy
from tests.services.helpers import at_km, names, save_institutions, search

FULLWIDTH_PERCENT = "\uff05"


def test_cause_text_keeps_any_chosen_cause_inside_the_radius_nearest_first(
    db_session: Session,
) -> None:
    save_institutions(
        db_session,
        at_km("Idosos", 3, causes=[Cause.ELDERLY, Cause.HEALTH]),
        at_km("Animais", 1, causes=[Cause.ANIMALS]),
        at_km("Escola", 2, causes=[Cause.EDUCATION]),
        at_km("Animais longe", 30, causes=[Cause.ANIMALS]),
    )
    filters = SearchFilters(max_distance_km=10, causes=(Cause.ANIMALS, Cause.ELDERLY))

    assert names(search(db_session, CauseTextStrategy, filters)) == ["Animais", "Idosos"]


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("sao", ["Associação São Francisco", "Abrigo Sao Jose"]),
        ("ABRIGO SÃO JOSÉ", ["Abrigo Sao Jose"]),
        ("lar esperanca", ["Associação São Francisco"]),
    ],
)
def test_cause_text_finds_either_name_ignoring_case_and_accents(
    db_session: Session, text: str, found: list[str]
) -> None:
    save_institutions(
        db_session,
        at_km("Associação São Francisco", 1, trade_name="Lar Esperança"),
        at_km("Abrigo Sao Jose", 2),
        at_km("Casa do Pão", 3),
    )

    assert names(search(db_session, CauseTextStrategy, SearchFilters(text=text))) == found


@pytest.mark.parametrize(
    ("text", "found"),
    [("100%", ["Casa 100%"]), (FULLWIDTH_PERCENT, ["Casa 100%"]), ("_", []), ("\\", [])],
)
def test_cause_text_treats_percent_underscore_and_backslash_as_plain_text(
    db_session: Session, text: str, found: list[str]
) -> None:
    save_institutions(db_session, at_km("Casa 100%", 1), at_km("Casa 1000", 2))

    assert names(search(db_session, CauseTextStrategy, SearchFilters(text=text))) == found
