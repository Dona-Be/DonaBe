import pytest

from src.domain.exceptions import InvalidCepError
from src.models.user import Donor, Manager, User

PHONE_MESSAGE = "Não é um número de telefone válido."


@pytest.mark.parametrize("user_class", [Donor, Manager])
@pytest.mark.parametrize(
    ("phone", "digits"),
    [("(11) 99999-0000", "11999990000"), ("(11) 2000-0000", "1120000000")],
    ids=["cellphone", "landline"],
)
def test_the_phone_of_any_user_keeps_only_the_digits(
    user_class: type[User], phone: str, digits: str
) -> None:
    assert user_class(phone=phone).phone == digits


def test_an_invalid_phone_is_rejected() -> None:
    with pytest.raises(ValueError, match=PHONE_MESSAGE):
        Donor(phone="(11) 9999-000")


@pytest.mark.parametrize("postal_code", ["01310-200", " 01310200 "])
def test_the_postal_code_of_a_donor_keeps_only_the_digits(postal_code: str) -> None:
    assert Donor(postal_code=postal_code).postal_code == "01310200"


def test_an_invalid_postal_code_is_rejected() -> None:
    with pytest.raises(InvalidCepError):
        Donor(postal_code="0131020")


@pytest.mark.parametrize(
    ("attribute", "value"), [("phone", "(11) 99999-0000"), ("postal_code", "01310-200")]
)
def test_an_optional_field_can_be_cleared(attribute: str, value: str) -> None:
    donor = Donor(**{attribute: value})

    setattr(donor, attribute, None)

    assert getattr(donor, attribute) is None


@pytest.mark.parametrize("attribute", ["postal_code", "location", "preferred_causes"])
def test_a_manager_has_none_of_the_donor_fields(attribute: str) -> None:
    # Single-table inheritance: the donor columns exist in the users table, but not in Manager.
    with pytest.raises(TypeError, match=attribute):
        Manager(**{attribute: None})
