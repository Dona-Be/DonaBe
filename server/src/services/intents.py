from datetime import datetime

from src.domain.enums import DonationIntentStatus, NeedStatus, NotificationType, Role
from src.domain.exceptions import (
    ActiveIntentAlreadyExistsError,
    InstitutionNotFoundError,
    IntentNotFoundError,
    NeedNotFoundError,
    NeedNotOpenForIntentError,
    NotInstitutionManagerError,
    NotIntentDonorError,
)
from src.models.donation_intent import DonationIntent
from src.models.institution import Institution
from src.models.need import Need
from src.models.user import Donor, Manager, User
from src.repositories.institutions import InstitutionRepository
from src.repositories.intents import IntentRepository
from src.repositories.needs import NeedRepository
from src.services.intent_events import IntentEvent, IntentEventPublisher
from src.services.intent_states import state_of


class IntentService:
    def __init__(
        self,
        repository: IntentRepository,
        needs: NeedRepository,
        institutions: InstitutionRepository,
        publisher: IntentEventPublisher,
    ) -> None:
        self._repository = repository
        self._needs = needs
        self._institutions = institutions
        self._publisher = publisher

    def register(self, donor: Donor, need_id: int, message: str | None) -> DonationIntent:
        need = self._find_need(need_id)
        if need.status != NeedStatus.OPEN:
            raise NeedNotOpenForIntentError()
        if self._repository.find_active(need_id, donor.id) is not None:
            raise ActiveIntentAlreadyExistsError()
        intent = DonationIntent(
            need=need,
            donor=donor,
            status=DonationIntentStatus.REGISTERED,
            message=message,
        )
        self._repository.save(intent)
        self._publish(
            intent,
            NotificationType.INTENT_REGISTERED,
            Role.DONOR,
            previous_status=None,
        )
        return intent

    def list_for_donor(self, donor: Donor) -> list[DonationIntent]:
        return self._repository.list_by_donor(donor.id)

    def list_for_institution(
        self,
        manager: Manager,
        institution_id: int,
        status: DonationIntentStatus | None,
    ) -> list[DonationIntent]:
        institution = self._find_institution(institution_id)
        self._check_institution_owner(manager, institution)
        return self._repository.list_by_institution(institution_id, status)

    def contact(self, manager: Manager, intent_id: int) -> DonationIntent:
        intent = self._find_intent(intent_id)
        self._check_institution_owner(manager, intent.need.institution)
        return self._transition(intent, "start_contact", Role.MANAGER)

    def schedule(self, manager: Manager, intent_id: int, delivery_date: datetime) -> DonationIntent:
        intent = self._find_intent(intent_id)
        self._check_institution_owner(manager, intent.need.institution)
        return self._transition(
            intent,
            "schedule_delivery",
            Role.MANAGER,
            date=delivery_date,
        )

    def deliver(self, donor: Donor, intent_id: int) -> DonationIntent:
        intent = self._find_intent(intent_id)
        self._check_donor(donor, intent)
        return self._transition(intent, "mark_delivered", Role.DONOR)

    def receive(self, manager: Manager, intent_id: int) -> DonationIntent:
        intent = self._find_intent(intent_id)
        self._check_institution_owner(manager, intent.need.institution)
        return self._transition(intent, "confirm_receipt", Role.MANAGER)

    def cancel(self, actor: User, intent_id: int) -> DonationIntent:
        intent = self._find_intent(intent_id)
        if isinstance(actor, Donor):
            self._check_donor(actor, intent)
        else:
            self._check_institution_owner(actor, intent.need.institution)
        return self._transition(intent, "cancel", actor.role)

    def _transition(
        self,
        intent: DonationIntent,
        method: str,
        actor: Role,
        **arguments: object,
    ) -> DonationIntent:
        previous_status = intent.status
        state = state_of(intent)
        getattr(state, method)(actor, **arguments)
        self._repository.save(intent)
        notification_type = (
            NotificationType.INTENT_CANCELLED
            if intent.status == DonationIntentStatus.CANCELLED
            else NotificationType.INTENT_DELIVERED
            if intent.status == DonationIntentStatus.DELIVERED
            else NotificationType.INTENT_STATUS_CHANGED
        )
        self._publish(intent, notification_type, actor, previous_status)
        return intent

    def _publish(
        self,
        intent: DonationIntent,
        notification_type: NotificationType,
        actor: Role,
        previous_status: DonationIntentStatus | None,
    ) -> None:
        self._publisher.notify(
            IntentEvent(
                notification_type,
                intent,
                actor,
                previous_status,
                intent.status,
            )
        )

    def _find_need(self, need_id: int) -> Need:
        need = self._needs.find_by_id(need_id)
        if need is None:
            raise NeedNotFoundError()
        return need

    def _find_institution(self, institution_id: int) -> Institution:
        institution = self._institutions.find_by_id(institution_id)
        if institution is None:
            raise InstitutionNotFoundError()
        return institution

    def _find_intent(self, intent_id: int) -> DonationIntent:
        intent = self._repository.find_by_id(intent_id)
        if intent is None:
            raise IntentNotFoundError()
        return intent

    def _check_donor(self, donor: Donor, intent: DonationIntent) -> None:
        if intent.donor_id != donor.id:
            raise NotIntentDonorError()

    def _check_institution_owner(self, manager: Manager, institution: Institution) -> None:
        if institution.manager_id != manager.id:
            raise NotInstitutionManagerError()
