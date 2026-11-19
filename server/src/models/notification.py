from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import NotificationType
from src.models.base import Base, created_at_column, enum_type

if TYPE_CHECKING:
    from src.models.donation_intent import DonationIntent
    from src.models.user import User

NOTIFICATIONS_BY_RECIPIENT_INDEX = "ix_notifications_recipient_id_read_at"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index(NOTIFICATIONS_BY_RECIPIENT_INDEX, "recipient_id", "read_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[NotificationType] = mapped_column(enum_type(NotificationType))
    donation_intent_id: Mapped[int] = mapped_column(ForeignKey("donation_intents.id"), index=True)
    message: Mapped[str]
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_column()

    recipient: Mapped["User"] = relationship()
    donation_intent: Mapped["DonationIntent"] = relationship()
