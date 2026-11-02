import pytest

from src.domain.cnpj import normalize_cnpj
from src.domain.exceptions import InvalidCnpjError
from tests.helpers import fullwidth


@pytest.mark.parametrize(
    ("cnpj", "tax_id"),
    [
        ("00.000.000/0001-91", "00000000000191"),
        (" 00000000000191 ", "00000000000191"),
        ("00.000.000/E08G-12", "00000000E08G12"),
        ("00000000e08g12", "00000000E08G12"),
        ("00,000,000/0001-91", "00000000000191"),
        ("00_000_000_0001_91", "00000000000191"),
    ],
    ids=["punctuated", "with spaces", "alphanumeric", "lower case", "commas", "underscores"],
)
def test_normalize_cnpj_strips_separators_and_upper_cases(cnpj: str, tax_id: str) -> None:
    assert normalize_cnpj(cnpj) == tax_id


# Itaú and Caixa: remainders 1 and 0 give a first check digit of zero.
@pytest.mark.parametrize(
    "cnpj", ["60701190000104", "00360305000104"], ids=["remainder one", "remainder zero"]
)
def test_normalize_cnpj_accepts_a_check_digit_of_zero(cnpj: str) -> None:
    assert normalize_cnpj(cnpj) == cnpj


@pytest.mark.parametrize(
    "cnpj",
    [
        "",
        "00000000000190",
        "00000000000181",
        "00000000E08G13",
        fullwidth("00000000000191"),
        "0000000000ß16",
        "0000000000019100000000000191",
    ],
    ids=[
        "empty",
        "wrong second check digit",
        "wrong first check digit",
        "alphanumeric with wrong check digit",
        "non ascii digits",
        "non ascii letter",
        "pasted twice",
    ],
)
def test_normalize_cnpj_rejects_invalid_values(cnpj: str) -> None:
    with pytest.raises(InvalidCnpjError):
        normalize_cnpj(cnpj)
