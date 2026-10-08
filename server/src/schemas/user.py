from pydantic import BaseModel, ConfigDict

from src.domain.enums import Role


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    picture_url: str | None
    role: Role


class PendingSignup(BaseModel):
    email: str
    name: str
    picture_url: str | None


class RoleChoice(BaseModel):
    role: Role
