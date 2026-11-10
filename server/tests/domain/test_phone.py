import pytest

from src.domain.exceptions import InvalidPhoneError
from src.domain.phone import validate_cellphone, validate_cellphone_or_landline, validate_landline
from tests.helpers import fullwidth


@pytest.mark.parametrize("number", ["(11) 99999-0000", "11 99999 0000", "11999990000"])
def test_validate_cellphone_keeps_only_the_digits(number: str) -> None:
    assert validate_cellphone(number) == "11999990000"


@pytest.mark.parametrize(
    "number",
    ["(11) 944-402", "(11) 2000-0000", fullwidth("11999990000"), "(25) 99999-0000"],
    ids=["too short", "landline", "non ascii digits", "unknown area code"],
)
def test_validate_cellphone_rejects_invalid_numbers(number: str) -> None:
    with pytest.raises(InvalidPhoneError):
        validate_cellphone(number)


@pytest.mark.parametrize("number", ["(11) 2000-0000", "11 2000 0000", "1120000000"])
def test_validate_landline_keeps_only_the_digits(number: str) -> None:
    assert validate_landline(number) == "1120000000"


@pytest.mark.parametrize(
    "number",
    ["(11) 2000-000", "(11) 99999-0000", "(25) 2000-0000"],
    ids=["too short", "cellphone", "unknown area code"],
)
def test_validate_landline_rejects_invalid_numbers(number: str) -> None:
    with pytest.raises(InvalidPhoneError):
        validate_landline(number)


@pytest.mark.parametrize(
    ("number", "digits"),
    [
        ("(11) 99999-0000", "11999990000"),
        ("11999990000", "11999990000"),
        ("(11) 2000-0000", "1120000000"),
        ("1120000000", "1120000000"),
    ],
    ids=["formatted cellphone", "cellphone digits", "formatted landline", "landline digits"],
)
def test_validate_cellphone_or_landline_keeps_only_the_digits(number: str, digits: str) -> None:
    assert validate_cellphone_or_landline(number) == digits


@pytest.mark.parametrize(
    "number",
    [
        "(11) 2000-000",
        "(11) 99999-00000",
        "(11) 9000-0000",
        "(11) 6000-0000",
        fullwidth("11999990000"),
        "(25) 99999-0000",
    ],
    ids=[
        "too short",
        "too long",
        "ten digits starting with 9",
        "landline starting with 6",
        "non ascii digits",
        "unknown area code",
    ],
)
def test_validate_cellphone_or_landline_rejects_invalid_numbers(number: str) -> None:
    with pytest.raises(InvalidPhoneError):
        validate_cellphone_or_landline(number)
