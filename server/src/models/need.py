from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import NeedStatus, NeedType
from src.models.base import Base, created_at_column, enum_type

if TYPE_CHECKING:
    from src.models.donation_intent import DonationIntent
    from src.models.institution import Institution

NEEDS_BY_STATUS_INDEX = "ix_needs_institution_id_status"


class Need(Base):
    __tablename__ = "needs"
    __table_args__ = (Index(NEEDS_BY_STATUS_INDEX, "institution_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"))
    title: Mapped[str]
    description: Mapped[str]
    type: Mapped[NeedType] = mapped_column(enum_type(NeedType), index=True)
    quantity: Mapped[str | None]
    status: Mapped[NeedStatus] = mapped_column(enum_type(NeedStatus))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_column()

    institution: Mapped["Institution"] = relationship()
    donation_intents: Mapped[list["DonationIntent"]] = relationship(
        back_populates="need", order_by="DonationIntent.id"
    )
