from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.domain.enums import NotificationType


class PublicNotification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    message: str
    donation_intent_id: int
    read_at: datetime | None
    created_at: datetime


class UnreadCount(BaseModel):
    count: int
