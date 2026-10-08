from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import ACTIVE_INTENT_STATUSES, DonationIntentStatus
from src.models.base import Base, created_at_column, enum_type

if TYPE_CHECKING:
    from src.models.need import Need
    from src.models.user import Donor

UNIQUE_ACTIVE_INTENT_INDEX = "uq_donation_intents_active_per_donor"
ACTIVE_STATUSES_SQL = ", ".join(f"'{status}'" for status in sorted(ACTIVE_INTENT_STATUSES))
ACTIVE_INTENT_CONDITION = text(f"status IN ({ACTIVE_STATUSES_SQL})")


class DonationIntent(Base):
    __tablename__ = "donation_intents"
    __table_args__ = (
        Index(
            UNIQUE_ACTIVE_INTENT_INDEX,
            "need_id",
            "donor_id",
            unique=True,
            postgresql_where=ACTIVE_INTENT_CONDITION,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    need_id: Mapped[int] = mapped_column(ForeignKey("needs.id"), index=True)
    donor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[DonationIntentStatus] = mapped_column(enum_type(DonationIntentStatus))
    donor_name: Mapped[str | None]
    donor_email: Mapped[str | None]
    phone: Mapped[str | None]
    message: Mapped[str | None]
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_retention_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    data_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_column()

    need: Mapped["Need"] = relationship(back_populates="donation_intents")
    donor: Mapped["Donor | None"] = relationship()
