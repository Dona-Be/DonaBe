import pytest

from src.domain.phone import validate_cellphone, validate_landline
from tests.helpers import fullwidth

CELLPHONE_MESSAGE = "Não é um número de celular válido."
LANDLINE_MESSAGE = "Não é um número de telefone fixo válido."


@pytest.mark.parametrize("number", ["(11) 99999-0000", "11 99999 0000", "11999990000"])
def test_validate_cellphone_keeps_only_the_digits(number: str) -> None:
    assert validate_cellphone(number) == "11999990000"


@pytest.mark.parametrize(
    ("number", "error_message"),
    [
        ("(11) 944-402", CELLPHONE_MESSAGE),
        ("(11) 2000-0000", CELLPHONE_MESSAGE),
        (fullwidth("11999990000"), CELLPHONE_MESSAGE),
        ("(25) 99999-0000", "O DDD 25 é inválido."),
    ],
    ids=["too short", "landline", "non ascii digits", "unknown area code"],
)
def test_validate_cellphone_rejects_invalid_numbers(number: str, error_message: str) -> None:
    with pytest.raises(ValueError, match=error_message):
        validate_cellphone(number)


@pytest.mark.parametrize("number", ["(11) 2000-0000", "11 2000 0000", "1120000000"])
def test_validate_landline_keeps_only_the_digits(number: str) -> None:
    assert validate_landline(number) == "1120000000"


@pytest.mark.parametrize(
    ("number", "error_message"),
    [
        ("(11) 2000-000", LANDLINE_MESSAGE),
        ("(11) 99999-0000", LANDLINE_MESSAGE),
        ("(25) 2000-0000", "O DDD 25 é inválido."),
    ],
    ids=["too short", "cellphone", "unknown area code"],
)
def test_validate_landline_rejects_invalid_numbers(number: str, error_message: str) -> None:
    with pytest.raises(ValueError, match=error_message):
        validate_landline(number)
