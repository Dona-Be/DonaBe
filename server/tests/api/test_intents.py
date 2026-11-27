from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.enums import DonationIntentStatus, NeedStatus, NotificationType
from src.models.need import Need
from src.models.notification import Notification
from src.models.user import Donor, Manager
from tests.api.helpers import GOOGLE_CALLBACK
from tests.fakes import USER_EMAIL
from tests.models.helpers import new_institution, register_intent, save_donor, save_need


@pytest.fixture
def donor_client(client: TestClient, db_session: Session) -> TestClient:
    save_donor(db_session)
    client.get(GOOGLE_CALLBACK, follow_redirects=False)
    return client


def test_donor_registers_lists_and_repeated_interest(
    donor_client: TestClient, db_session: Session
) -> None:
    need = save_need(db_session)

    response = donor_client.post(
        f"/api/needs/{need.id}/intents",
        json={"message": "Posso entregar nesta semana."},
    )

    assert response.status_code == 201
    [intent] = donor_client.get("/api/intents/me").json()
    assert intent["need_id"] == need.id
    assert intent["status"] == "registered"
    assert intent["message"] == "Posso entregar nesta semana."

    repeated = donor_client.post(f"/api/needs/{need.id}/intents")
    assert repeated.status_code == 409
    assert repeated.json() == {"detail": "Já existe uma intenção ativa para esta necessidade."}


def test_closed_need_rejects_a_new_interest(donor_client: TestClient, db_session: Session) -> None:
    need = save_need(db_session)
    need.status = NeedStatus.CLOSED
    db_session.commit()

    response = donor_client.post(f"/api/needs/{need.id}/intents")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "A necessidade não está aberta para receber intenções de doação."
    }


def owned_need(db_session: Session, manager_email: str = USER_EMAIL) -> Need:
    manager = db_session.scalar(select(Manager).where(Manager.email == manager_email))
    assert manager is not None
    need = Need(
        institution=new_institution(manager),
        title="Ração",
        description="Ração para cães adultos",
        status=NeedStatus.OPEN,
    )
    db_session.add(need)
    db_session.commit()
    return need


def test_registration_requires_authentication(client: TestClient) -> None:
    unauthenticated = client.post("/api/needs/1/intents")

    assert unauthenticated.status_code == 401


def test_registration_requires_donor(manager_client: TestClient) -> None:
    manager = manager_client.post("/api/needs/1/intents")

    assert manager.status_code == 403
    assert manager.json() == {"detail": "Acesso permitido apenas para doadores."}


def test_registration_of_missing_need_returns_not_found(donor_client: TestClient) -> None:
    response = donor_client.post("/api/needs/999/intents")

    assert response.status_code == 404
    assert response.json() == {"detail": "Necessidade não encontrada."}


def test_registration_publishes_notification_for_institution_manager(
    donor_client: TestClient, db_session: Session
) -> None:
    need = save_need(db_session)

    response = donor_client.post(f"/api/needs/{need.id}/intents")

    assert response.status_code == 201
    notification = db_session.scalar(
        select(Notification).where(
            Notification.recipient_id == need.institution.manager_id,
            Notification.type == NotificationType.INTENT_REGISTERED,
        )
    )
    assert notification is not None
    assert notification.donation_intent_id == response.json()["id"]
    assert notification.message == "Maria quer doar para a necessidade Ração."


def test_donor_intent_list_only_contains_their_own_intents(
    donor_client: TestClient, db_session: Session
) -> None:
    need = save_need(db_session)
    donor = db_session.scalar(select(Donor).where(Donor.email == USER_EMAIL))
    another_donor = save_donor(db_session, "outra@exemplo.com")
    assert donor is not None
    owned = register_intent(db_session, need, donor)
    register_intent(db_session, need, another_donor)

    response = donor_client.get("/api/intents/me")

    assert response.status_code == 200
    assert [intent["id"] for intent in response.json()] == [owned.id]


def test_manager_lists_own_institution_intents_with_status_filter(
    manager_client: TestClient, db_session: Session
) -> None:
    need = owned_need(db_session)
    first_donor = save_donor(db_session, "primeiro@exemplo.com")
    second_donor = save_donor(db_session, "segundo@exemplo.com")
    registered = register_intent(db_session, need, first_donor)
    in_contact = register_intent(db_session, need, second_donor, DonationIntentStatus.IN_CONTACT)
    path = f"/api/institutions/{need.institution_id}/intents"

    all_intents = manager_client.get(path)
    filtered = manager_client.get(path, params={"status": "in_contact"})

    assert all_intents.status_code == 200
    assert [intent["id"] for intent in all_intents.json()] == [in_contact.id, registered.id]
    assert [intent["id"] for intent in filtered.json()] == [in_contact.id]


def test_manager_cannot_list_another_institutions_intents(
    manager_client: TestClient, db_session: Session
) -> None:
    need = save_need(db_session)

    response = manager_client.get(f"/api/institutions/{need.institution_id}/intents")

    assert response.status_code == 403
    assert response.json() == {"detail": "Apenas o gestor da instituição pode editá-la."}


def test_manager_contact_and_schedule_transitions_publish_donor_notifications(
    manager_client: TestClient, db_session: Session
) -> None:
    need = owned_need(db_session)
    donor = save_donor(db_session, "doador@exemplo.com")
    intent = register_intent(db_session, need, donor)

    contacted = manager_client.post(f"/api/intents/{intent.id}/contact")
    scheduled = manager_client.post(
        f"/api/intents/{intent.id}/schedule",
        json={"date": "2030-01-15T10:00:00-03:00"},
    )

    assert contacted.status_code == 200
    assert contacted.json()["status"] == "in_contact"
    assert contacted.json()["contacted_at"] is not None
    assert scheduled.status_code == 200
    assert scheduled.json()["status"] == "delivery_scheduled"
    scheduled_for = datetime.fromisoformat(scheduled.json()["scheduled_for"].replace("Z", "+00:00"))
    assert scheduled_for.astimezone(UTC) == datetime(2030, 1, 15, 13, tzinfo=UTC)
    notices = list(
        db_session.scalars(
            select(Notification)
            .where(Notification.recipient_id == donor.id)
            .order_by(Notification.id)
        )
    )
    assert [notice.message for notice in notices] == [
        "Sua doação para a necessidade Ração mudou para Em contato.",
        "Sua doação para a necessidade Ração mudou para Entrega agendada.",
    ]


def test_manager_cannot_schedule_a_past_delivery(
    manager_client: TestClient, db_session: Session
) -> None:
    need = owned_need(db_session)
    donor = save_donor(db_session, "doador@exemplo.com")
    intent = register_intent(db_session, need, donor, DonationIntentStatus.IN_CONTACT)

    response = manager_client.post(
        f"/api/intents/{intent.id}/schedule",
        json={"scheduled_for": "2020-01-01T10:00:00Z"},
    )

    assert response.status_code == 409
    db_session.refresh(intent)
    assert intent.status is DonationIntentStatus.IN_CONTACT


def test_only_the_intent_donor_can_mark_it_delivered(
    donor_client: TestClient, db_session: Session
) -> None:
    need = save_need(db_session)
    donor = db_session.scalar(select(Donor).where(Donor.email == USER_EMAIL))
    other_donor = save_donor(db_session, "outra@exemplo.com")
    assert donor is not None
    intent = register_intent(db_session, need, other_donor, DonationIntentStatus.DELIVERY_SCHEDULED)

    response = donor_client.post(f"/api/intents/{intent.id}/deliver")

    assert response.status_code == 403
    db_session.refresh(intent)
    assert intent.status is DonationIntentStatus.DELIVERY_SCHEDULED


def test_donor_marks_delivery(donor_client: TestClient, db_session: Session) -> None:
    need = save_need(db_session)
    donor = db_session.scalar(select(Donor).where(Donor.email == USER_EMAIL))
    assert donor is not None
    intent = register_intent(db_session, need, donor, DonationIntentStatus.DELIVERY_SCHEDULED)

    delivered = donor_client.post(f"/api/intents/{intent.id}/deliver")

    assert delivered.status_code == 200
    assert delivered.json()["status"] == "delivered"
    assert delivered.json()["delivered_at"] is not None


def test_manager_confirms_receipt(manager_client: TestClient, db_session: Session) -> None:
    need = owned_need(db_session)
    donor = save_donor(db_session, "doador@exemplo.com")
    intent = register_intent(db_session, need, donor, DonationIntentStatus.DELIVERED)

    received = manager_client.post(f"/api/intents/{intent.id}/receive")

    assert received.status_code == 200
    assert received.json()["status"] == "received"
    assert received.json()["received_at"] is not None
    db_session.refresh(intent)
    assert intent.status is DonationIntentStatus.RECEIVED


@pytest.mark.parametrize(
    "initial_status",
    [
        DonationIntentStatus.REGISTERED,
        DonationIntentStatus.IN_CONTACT,
        DonationIntentStatus.DELIVERED,
    ],
)
def test_invalid_intent_transitions_return_conflict(
    initial_status: DonationIntentStatus,
    donor_client: TestClient,
    db_session: Session,
) -> None:
    donor = db_session.scalar(select(Donor).where(Donor.email == USER_EMAIL))
    assert donor is not None
    intent = register_intent(db_session, save_need(db_session), donor, initial_status)

    response = donor_client.post(f"/api/intents/{intent.id}/deliver")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Não é possível fazer essa mudança de status na intenção de doação."
    }
    db_session.refresh(intent)
    assert intent.status is initial_status


def test_donor_can_cancel_own_intent_and_get_notified(
    donor_client: TestClient, db_session: Session
) -> None:
    need = save_need(db_session)
    donor = db_session.scalar(select(Donor).where(Donor.email == USER_EMAIL))
    assert donor is not None
    intent = register_intent(db_session, need, donor)

    response = donor_client.post(f"/api/intents/{intent.id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancelled_by"] == "donor"
    notification = db_session.scalar(
        select(Notification).where(
            Notification.recipient_id == need.institution.manager_id,
            Notification.type == NotificationType.INTENT_CANCELLED,
        )
    )
    assert notification is not None


def test_cancel_of_missing_intent_returns_not_found(donor_client: TestClient) -> None:
    response = donor_client.post("/api/intents/999/cancel")

    assert response.status_code == 404
    assert response.json() == {"detail": "Intenção de doação não encontrada."}


def test_intent_endpoints_require_authentication(client: TestClient) -> None:
    responses = [
        client.get("/api/intents/me"),
        client.get("/api/institutions/1/intents"),
        client.post("/api/intents/1/contact"),
        client.post("/api/intents/1/schedule", json={"date": "2030-01-01T00:00:00Z"}),
        client.post("/api/intents/1/deliver"),
        client.post("/api/intents/1/receive"),
        client.post("/api/intents/1/cancel"),
    ]

    assert [response.status_code for response in responses] == [401] * len(responses)
