from datetime import datetime
from typing import TYPE_CHECKING, Self

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import Role
from src.domain.user_profile import UserProfile
from src.models.base import Base, created_at_column, enum_type

if TYPE_CHECKING:
    from src.models.institution import Institution

FIRST_SESSION_VERSION = 1


class User(Base):
    __tablename__ = "users"
    # Single-table inheritance: the role column decides whether a row becomes a Donor or a
    # Manager, and User itself is never instantiated.
    __mapper_args__ = {"polymorphic_on": "role", "polymorphic_abstract": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    picture_url: Mapped[str | None]
    role: Mapped[Role] = mapped_column(enum_type(Role))
    session_version: Mapped[int] = mapped_column(server_default=str(FIRST_SESSION_VERSION))
    created_at: Mapped[datetime] = created_at_column()

    @classmethod
    def from_profile(cls, profile: UserProfile) -> Self:
        return cls(
            email=profile.email,
            name=profile.name,
            picture_url=profile.picture_url,
            session_version=FIRST_SESSION_VERSION,
        )

    def end_sessions(self) -> None:
        # Tokens carry the version they were issued with, so bumping it logs out every device.
        self.session_version += 1


class Donor(User):
    __mapper_args__ = {"polymorphic_identity": Role.DONOR}


class Manager(User):
    __mapper_args__ = {"polymorphic_identity": Role.MANAGER}

    institutions: Mapped[list["Institution"]] = relationship(back_populates="manager")
