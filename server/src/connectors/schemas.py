from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from src.domain.cep import CEP_DIGITS
from src.domain.charity import RegistryCode, RegistryData
from src.domain.cnpj import TAX_ID_PATTERN

STATE_FORMAT = r"^[A-Z]{2}$"
LEGAL_NATURE_FORMAT = r"^[0-9]{4}$"
CNAE_FORMAT = r"^[0-9]{7}$"

# Every way a body can miss the shape a connector expects.
MALFORMED_BODY_ERRORS = (KeyError, IndexError, TypeError, AttributeError, ValidationError)


class StrictNumbers(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def reject_booleans(cls, value: object) -> object:
        # JSON true and false would otherwise count as the numbers 1 and 0.
        if isinstance(value, bool):
            raise ValueError("expected a number, not true or false")
        return value


class Coordinates(StrictNumbers):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class Route(StrictNumbers):
    distance_meters: float = Field(ge=0, allow_inf_nan=False)
    duration_seconds: float = Field(ge=0, allow_inf_nan=False)


class Address(BaseModel):
    postal_code: str | None = Field(default=None, pattern=CEP_DIGITS.pattern)
    state: str = Field(pattern=STATE_FORMAT)
    city: str = Field(min_length=1)
    neighborhood: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    coordinates: Coordinates | None = None


class Company(BaseModel):
    tax_id: str = Field(pattern=TAX_ID_PATTERN.pattern)
    legal_name: str = Field(min_length=1)
    trade_name: str | None = None
    registration_status: str = Field(min_length=1)
    legal_nature_code: str = Field(pattern=LEGAL_NATURE_FORMAT)
    legal_nature_description: str = Field(min_length=1)
    main_activity_code: str = Field(pattern=CNAE_FORMAT)
    main_activity_description: str = Field(min_length=1)
    address: Address
    raw_data: dict[str, Any]

    def registry_data(self) -> RegistryData:
        legal_nature = RegistryCode(self.legal_nature_code, self.legal_nature_description)
        main_activity = RegistryCode(self.main_activity_code, self.main_activity_description)
        return RegistryData(self.registration_status, legal_nature, main_activity)
