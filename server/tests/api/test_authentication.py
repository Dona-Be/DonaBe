from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.api.authentication import (
    CurrentDonor,
    CurrentManager,
    get_current_donor,
    get_current_manager,
)
from src.models.user import Donor, Manager, User
from tests.api.helpers import DONOR_SIGNUP, sign_up

GUARDS = [
    (get_current_donor, Donor, Manager, "Acesso permitido apenas para doadores."),
    (get_current_manager, Manager, Donor, "Acesso permitido apenas para gestores."),
]
ROUTES = [
    ("donor", DONOR_SIGNUP, "/donors", "/managers"),
    ("manager", None, "/managers", "/donors"),
]


def guarded_app() -> FastAPI:
    # A throwaway app, because no route of the other user stories exists yet.
    app = FastAPI()

    @app.get("/donors")
    def donors_only(donor: CurrentDonor) -> str:
        return donor.email

    @app.get("/managers")
    def managers_only(manager: CurrentManager) -> str:
        return manager.email

    return app


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


@pytest.mark.usefixtures("brasilapi")
@pytest.mark.parametrize(("role", "data", "own_route", "other_route"), ROUTES)
def test_a_guarded_route_answers_only_the_role_it_asks_for(
    client: TestClient, role: str, data: dict[str, Any] | None, own_route: str, other_route: str
) -> None:
    sign_up(client, role, data)
    guarded = TestClient(guarded_app(), cookies=client.cookies)

    assert guarded.get(own_route).status_code == 200
    assert guarded.get(other_route).status_code == 403


def test_a_guarded_route_asks_for_the_login_first() -> None:
    response = TestClient(guarded_app()).get("/donors")

    assert response.status_code == 401
    assert response.json() == {"detail": "Você precisa entrar para continuar."}
