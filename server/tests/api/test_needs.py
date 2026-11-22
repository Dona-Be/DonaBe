import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.enums import NeedStatus
from tests.api.helpers import GOOGLE_CALLBACK, INSTITUTIONS, register
from tests.models.helpers import save_need


def test_the_manager_creates_and_edits_a_need(manager_client: TestClient) -> None:
    institution = register(manager_client).json()
    path = f"{INSTITUTIONS}/{institution['id']}/needs"

    created = manager_client.post(
        path,
        json={"title": "Cobertores", "description": "Cobertores para o inverno", "quantity": "20"},
    )

    assert created.status_code == 201
    need = created.json()
    assert need == {
        "id": 1,
        "title": "Cobertores",
        "description": "Cobertores para o inverno",
        "quantity": "20",
        "status": "open",
        "closed_at": None,
    }

    edited = manager_client.patch(
        f"/api/needs/{need['id']}", json={"title": "Cobertores infantis", "quantity": None}
    )

    assert edited.status_code == 200
    assert edited.json() == {**need, "title": "Cobertores infantis"}
    cleared = manager_client.patch(
        f"/api/needs/{need['id']}", json={"title": None, "quantity": " "}
    )
    assert cleared.json() == {**edited.json(), "quantity": None}
    blank = manager_client.post(
        path, json={"title": "Ração", "description": "Ração", "quantity": " "}
    )
    assert blank.json()["quantity"] is None


def test_managers_can_only_change_needs_of_their_own_institution(
    manager_client: TestClient, db_session: Session
) -> None:
    need = save_need(db_session)

    create = manager_client.post(
        f"{INSTITUTIONS}/{need.institution_id}/needs",
        json={"title": "Ração", "description": "Ração para os animais"},
    )
    edit = manager_client.patch(f"/api/needs/{need.id}", json={"title": "Outro título"})
    fulfill = manager_client.post(f"/api/needs/{need.id}/fulfill")
    close = manager_client.post(f"/api/needs/{need.id}/close")

    assert [create.status_code, edit.status_code, fulfill.status_code, close.status_code] == [
        403,
        403,
        403,
        403,
    ]
    expected_error = {"detail": "Apenas o gestor da instituição pode alterar esta necessidade."}
    assert all(response.json() == expected_error for response in (create, edit, fulfill, close))
    db_session.refresh(need)
    assert need.title == "Ração"
    assert need.status is NeedStatus.OPEN
    assert need.closed_at is None


@pytest.mark.usefixtures("donor")
def test_need_routes_require_a_manager_for_changes(client: TestClient) -> None:
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    response = client.post("/api/needs/1/fulfill")

    assert response.status_code == 403
    assert response.json() == {"detail": "Acesso permitido apenas para gestores."}


def test_need_writes_return_not_found_for_missing_records(manager_client: TestClient) -> None:
    missing_institution = manager_client.post(
        f"{INSTITUTIONS}/1/needs", json={"title": "Ração", "description": "Para animais"}
    )
    missing_need = manager_client.patch("/api/needs/1", json={"title": "Ração"})

    assert missing_institution.status_code == 404
    assert missing_institution.json() == {"detail": "Instituição não encontrada."}
    assert missing_need.status_code == 404
    assert missing_need.json() == {"detail": "Necessidade não encontrada."}
