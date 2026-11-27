from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.enums import DonationIntentStatus


class NewIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str | None = Field(default=None, max_length=2000)


class ScheduleDelivery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: datetime | None = None
    scheduled_for: datetime | None = None

    @model_validator(mode="after")
    def require_one_delivery_date(self) -> "ScheduleDelivery":
        if (self.date is None) == (self.scheduled_for is None):
            raise ValueError("Informe uma data de entrega.")
        return self

    def delivery_date(self) -> datetime:
        value = self.date if self.date is not None else self.scheduled_for
        if value is None:
            raise ValueError("Informe uma data de entrega.")
        return value


class PublicIntent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: DonationIntentStatus
    message: str | None
    need_id: int
    donor_id: int
    contacted_at: datetime | None
    scheduled_for: datetime | None
    delivered_at: datetime | None
    received_at: datetime | None
    cancelled_at: datetime | None
    cancelled_by: str | None
    created_at: datetime
