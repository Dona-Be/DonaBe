from typing import Annotated

from fastapi import APIRouter, Query

from src.api.authentication import CurrentDonor, CurrentManager, CurrentUser
from src.api.dependencies import IntentServiceDep
from src.api.parameters import DatabaseId
from src.domain.enums import DonationIntentStatus
from src.models.donation_intent import DonationIntent
from src.schemas.intent import NewIntent, PublicIntent, ScheduleDelivery

router = APIRouter(tags=["intents"])


@router.post(
    "/needs/{need_id}/intents",
    status_code=201,
    response_model=PublicIntent,
    summary="Register interest in an open need",
)
def register_intent(
    need_id: DatabaseId,
    donor: CurrentDonor,
    service: IntentServiceDep,
    data: NewIntent | None = None,
) -> DonationIntent:
    message = None if data is None else data.message
    return service.register(donor, need_id, message)


@router.get(
    "/intents/me",
    response_model=list[PublicIntent],
    summary="List the current donor's interests",
)
def list_my_intents(
    donor: CurrentDonor,
    service: IntentServiceDep,
) -> list[DonationIntent]:
    return service.list_for_donor(donor)


@router.get(
    "/institutions/{institution_id}/intents",
    response_model=list[PublicIntent],
    summary="List interests received by an institution",
)
def list_institution_intents(
    institution_id: DatabaseId,
    manager: CurrentManager,
    service: IntentServiceDep,
    status: Annotated[DonationIntentStatus | None, Query()] = None,
) -> list[DonationIntent]:
    return service.list_for_institution(manager, institution_id, status)


@router.post(
    "/intents/{intent_id}/contact",
    response_model=PublicIntent,
    summary="Move an interest to in contact",
)
def contact_intent(
    intent_id: DatabaseId,
    manager: CurrentManager,
    service: IntentServiceDep,
) -> DonationIntent:
    return service.contact(manager, intent_id)


@router.post(
    "/intents/{intent_id}/schedule",
    response_model=PublicIntent,
    summary="Schedule delivery for an interest",
)
def schedule_intent(
    intent_id: DatabaseId,
    data: ScheduleDelivery,
    manager: CurrentManager,
    service: IntentServiceDep,
) -> DonationIntent:
    return service.schedule(manager, intent_id, data.delivery_date())


@router.post(
    "/intents/{intent_id}/deliver",
    response_model=PublicIntent,
    summary="Mark an interest as delivered",
)
def deliver_intent(
    intent_id: DatabaseId,
    donor: CurrentDonor,
    service: IntentServiceDep,
) -> DonationIntent:
    return service.deliver(donor, intent_id)


@router.post(
    "/intents/{intent_id}/receive",
    response_model=PublicIntent,
    summary="Confirm receipt of an interest",
)
def receive_intent(
    intent_id: DatabaseId,
    manager: CurrentManager,
    service: IntentServiceDep,
) -> DonationIntent:
    return service.receive(manager, intent_id)


@router.post(
    "/intents/{intent_id}/cancel",
    response_model=PublicIntent,
    summary="Cancel an interest",
)
def cancel_intent(
    intent_id: DatabaseId,
    actor: CurrentUser,
    service: IntentServiceDep,
) -> DonationIntent:
    return service.cancel(actor, intent_id)
