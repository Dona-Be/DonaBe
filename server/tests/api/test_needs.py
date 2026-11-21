from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.enums import NeedStatus
from src.models.need import Need
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
        f"/api/needs/{need['id']}", json={"title": "Cobertores infantis", "quantity": "12"}
    )

    assert edited.status_code == 200
    assert edited.json() == {
        **need,
        "title": "Cobertores infantis",
        "quantity": "12",
    }
    cleared = manager_client.patch(
        f"/api/needs/{need['id']}", json={"title": None, "quantity": None}
    )
    assert cleared.json() == {**edited.json(), "quantity": None}


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


@pytest.mark.parametrize(
    ("action", "new_status"), [("fulfill", NeedStatus.FULFILLED), ("close", NeedStatus.CLOSED)]
)
def test_the_manager_can_change_an_open_need_status_once(
    manager_client: TestClient,
    db_session: Session,
    action: str,
    new_status: NeedStatus,
) -> None:
    institution = register(manager_client).json()
    need = Need(
        institution_id=institution["id"],
        title="Ração",
        description="Ração para cães",
        status=NeedStatus.OPEN,
    )
    db_session.add(need)
    db_session.commit()

    response = manager_client.post(f"/api/needs/{need.id}/{action}")

    assert response.status_code == 200
    assert response.json()["status"] == new_status
    closed_at = datetime.fromisoformat(response.json()["closed_at"])
    assert closed_at.tzinfo is not None
    db_session.refresh(need)
    assert need.status is new_status
    assert need.closed_at is not None

    repeated = manager_client.post(f"/api/needs/{need.id}/close")

    assert repeated.status_code == 409
    assert repeated.json() == {"detail": "Apenas necessidades abertas podem mudar de status."}
    db_session.refresh(need)
    assert need.status is new_status


def test_only_the_owner_sees_non_open_needs_in_the_institution_list(
    manager_client: TestClient, client: TestClient, db_session: Session
) -> None:
    institution = register(manager_client).json()
    open_need = Need(
        institution_id=institution["id"],
        title="Ração",
        description="Ração para cães",
        status=NeedStatus.OPEN,
    )
    fulfilled_need = Need(
        institution_id=institution["id"],
        title="Coleiras",
        description="Coleiras para cães",
        status=NeedStatus.FULFILLED,
    )
    db_session.add_all([open_need, fulfilled_need])
    db_session.commit()
    list_path = f"{INSTITUTIONS}/{institution['id']}/needs"

    assert [need["title"] for need in manager_client.get(list_path).json()] == [
        "Ração",
        "Coleiras",
    ]
    open_needs = manager_client.get(list_path, params={"status": "open"}).json()
    assert [need["title"] for need in open_needs] == ["Ração"]

    manager_client.cookies.clear()
    public_needs = client.get(list_path)
    requested_fulfilled = client.get(list_path, params={"status": "fulfilled"})

    assert [need["title"] for need in public_needs.json()] == ["Ração"]
    assert requested_fulfilled.json() == []


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
