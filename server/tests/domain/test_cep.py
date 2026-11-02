import pytest

from src.domain.cep import normalize_cep
from src.domain.exceptions import InvalidCepError
from tests.helpers import fullwidth


@pytest.mark.parametrize("cep", ["01310200", "01310-200", " 01310200 "])
def test_normalize_cep_keeps_the_eight_digits(cep: str) -> None:
    assert normalize_cep(cep) == "01310200"


@pytest.mark.parametrize(
    "cep",
    ["", "1310200", "0131020a", "01310.200", "013102000", fullwidth("01310200")],
    ids=["empty", "seven digits", "letter", "dot", "nine digits", "non ascii digits"],
)
def test_normalize_cep_rejects_malformed_values(cep: str) -> None:
    with pytest.raises(InvalidCepError):
        normalize_cep(cep)
