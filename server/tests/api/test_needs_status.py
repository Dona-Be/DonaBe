from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.enums import NeedStatus
from src.models.need import Need
from tests.api.helpers import INSTITUTIONS, register
from tests.models.helpers import save_need


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
    other_need = save_need(db_session)
    closed_need = Need(
        institution_id=other_need.institution_id,
        title="Vacinas",
        description="Vacinas para cães",
        status=NeedStatus.CLOSED,
    )
    db_session.add(closed_need)
    db_session.commit()
    list_path = f"{INSTITUTIONS}/{institution['id']}/needs"

    assert [need["title"] for need in manager_client.get(list_path).json()] == [
        "Ração",
        "Coleiras",
    ]
    open_needs = manager_client.get(list_path, params={"status": "open"}).json()
    assert [need["title"] for need in open_needs] == ["Ração"]
    other_path = f"{INSTITUTIONS}/{other_need.institution_id}/needs"
    assert [need["title"] for need in manager_client.get(other_path).json()] == ["Ração"]

    manager_client.cookies.clear()
    public_needs = client.get(list_path)
    requested_fulfilled = client.get(list_path, params={"status": "fulfilled"})

    assert [need["title"] for need in public_needs.json()] == ["Ração"]
    assert requested_fulfilled.json() == []
