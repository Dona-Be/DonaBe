from abc import ABC, abstractmethod

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.enums import ACTIVE_INTENT_STATUSES, DonationIntentStatus
from src.domain.exceptions import ActiveIntentAlreadyExistsError
from src.models.donation_intent import DonationIntent
from src.models.need import Need


class IntentRepository(ABC):
    @abstractmethod
    def save(self, intent: DonationIntent) -> None: ...

    @abstractmethod
    def find_by_id(self, intent_id: int) -> DonationIntent | None: ...

    @abstractmethod
    def find_active(self, need_id: int, donor_id: int) -> DonationIntent | None: ...

    @abstractmethod
    def list_by_donor(self, donor_id: int) -> list[DonationIntent]: ...

    @abstractmethod
    def list_by_institution(
        self, institution_id: int, status: DonationIntentStatus | None
    ) -> list[DonationIntent]: ...


class SqlAlchemyIntentRepository(IntentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, intent: DonationIntent) -> None:
        self._session.add(intent)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if not isinstance(error.orig, UniqueViolation):
                raise
            raise ActiveIntentAlreadyExistsError() from error

    def find_by_id(self, intent_id: int) -> DonationIntent | None:
        return self._session.get(DonationIntent, intent_id)

    def find_active(self, need_id: int, donor_id: int) -> DonationIntent | None:
        query = (
            select(DonationIntent)
            .where(
                DonationIntent.need_id == need_id,
                DonationIntent.donor_id == donor_id,
                DonationIntent.status.in_(ACTIVE_INTENT_STATUSES),
            )
            .order_by(DonationIntent.id)
        )
        return self._session.scalars(query).first()

    def list_by_donor(self, donor_id: int) -> list[DonationIntent]:
        query = select(DonationIntent).where(DonationIntent.donor_id == donor_id)
        return list(self._session.scalars(query.order_by(DonationIntent.id.desc())))

    def list_by_institution(
        self, institution_id: int, status: DonationIntentStatus | None
    ) -> list[DonationIntent]:
        query = (
            select(DonationIntent)
            .join(Need, DonationIntent.need_id == Need.id)
            .where(Need.institution_id == institution_id)
        )
        if status is not None:
            query = query.where(DonationIntent.status == status)
        return list(self._session.scalars(query.order_by(DonationIntent.id.desc())))
