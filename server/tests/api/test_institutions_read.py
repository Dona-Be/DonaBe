import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.connectors.companies import company_from
from src.domain.enums import NeedStatus
from src.models.need import Need
from tests.api.helpers import (
    GOOGLE_CALLBACK,
    INSTITUTION,
    INSTITUTION_DETAILS,
    INSTITUTIONS,
    MY_INSTITUTIONS,
    register,
)
from tests.connectors.samples import AACD
from tests.fakes import FakeCompanyLookup
from tests.models.helpers import save_need

MANAGER_ROUTES = [
    ("GET", "/lookup?cnpj=60979457000111"),
    ("POST", ""),
    ("GET", "/me"),
    ("PATCH", "/1"),
]


def test_anyone_reads_the_public_page_of_an_institution(manager_client: TestClient) -> None:
    register(manager_client, **INSTITUTION_DETAILS)
    manager_client.cookies.clear()

    response = manager_client.get(f"{INSTITUTIONS}/1")

    assert response.status_code == 200
    assert response.json() == {**INSTITUTION, **INSTITUTION_DETAILS, "open_needs": []}


def test_the_public_page_lists_only_the_open_needs(client: TestClient, db_session: Session) -> None:
    need = save_need(db_session)
    for status in (NeedStatus.FULFILLED, NeedStatus.CLOSED, NeedStatus.OPEN):
        db_session.add(
            Need(institution=need.institution, title=status, description="", status=status)
        )
    db_session.commit()

    oldest, newest = client.get(f"{INSTITUTIONS}/{need.institution_id}").json()["open_needs"]

    assert oldest == {
        "id": need.id,
        "title": "Ração",
        "description": "Ração para cães adultos",
        "quantity": None,
    }
    assert newest["title"] == "open"


@pytest.mark.parametrize(("institution_id", "status"), [(1, 404), (2**31, 422), ("mine", 422)])
def test_the_public_page_needs_the_id_of_a_registered_institution(
    client: TestClient, institution_id: object, status: int
) -> None:
    assert client.get(f"{INSTITUTIONS}/{institution_id}").status_code == status


def test_the_manager_lists_only_their_own_institutions_from_the_oldest(
    manager_client: TestClient, companies: FakeCompanyLookup, db_session: Session
) -> None:
    save_need(db_session)
    first = register(manager_client).json()
    companies.answer = company_from("11444777000161", AACD)
    second = register(manager_client, "11.444.777/0001-61").json()

    response = manager_client.get(MY_INSTITUTIONS)

    assert response.status_code == 200
    assert response.json() == [first, second]


@pytest.mark.parametrize(("method", "path"), MANAGER_ROUTES)
def test_the_manager_routes_require_a_logged_in_user(
    client: TestClient, method: str, path: str
) -> None:
    response = client.request(method, INSTITUTIONS + path)

    assert response.status_code == 401
    assert response.json() == {"detail": "Você precisa entrar para continuar."}


@pytest.mark.usefixtures("donor")
@pytest.mark.parametrize(("method", "path"), MANAGER_ROUTES)
def test_the_manager_routes_refuse_a_donor(client: TestClient, method: str, path: str) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)

    response = client.request(method, INSTITUTIONS + path)

    assert response.status_code == 403
    assert response.json() == {"detail": "Acesso permitido apenas para gestores."}
