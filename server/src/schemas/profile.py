from pydantic import BaseModel, ConfigDict, Field

from src.domain.enums import Cause, Role

MAX_NAME_LENGTH = 100


class Profile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    name: str
    picture_url: str | None
    phone: str | None = None
    role: Role | None = None
    postal_code: str | None = None
    preferred_causes: list[Cause] | None = None


class NewDonor(BaseModel):
    postal_code: str
    preferred_causes: list[Cause] = Field(max_length=len(Cause))
    phone: str | None = None


class ProfileChanges(BaseModel):
    name: str | None = Field(default=None, pattern=r"\S", max_length=MAX_NAME_LENGTH)
    phone: str | None = None
    postal_code: str | None = None
    preferred_causes: list[Cause] | None = Field(default=None, max_length=len(Cause))
