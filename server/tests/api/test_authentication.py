from collections.abc import Callable

import pytest
from fastapi import HTTPException

from src.api.authentication import get_current_donor, get_current_manager
from src.models.user import Donor, Manager, User

GUARDS = [
    (get_current_donor, Donor, Manager, "Acesso permitido apenas para doadores."),
    (get_current_manager, Manager, Donor, "Acesso permitido apenas para gestores."),
]


@pytest.mark.parametrize(("guard", "allowed", "denied", "message"), GUARDS)
def test_a_role_guard_lets_only_its_role_through(
    guard: Callable[[User], User], allowed: type[User], denied: type[User], message: str
) -> None:
    user = allowed()

    assert guard(user) is user
    with pytest.raises(HTTPException) as error:
        guard(denied())

    assert error.value.status_code == 403
    assert error.value.detail == message
