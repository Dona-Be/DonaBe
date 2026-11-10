from datetime import datetime
from typing import TYPE_CHECKING, Self

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import CheckConstraint, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.domain.cep import normalize_cep
from src.domain.enums import Cause, Role
from src.domain.phone import validate_cellphone_or_landline
from src.domain.user_profile import UserProfile
from src.models.base import Base, created_at_column, enum_type
from src.models.institution import EMPTY_LIST, WGS84_SRID

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
    phone: Mapped[str | None] = mapped_column(
        String(11), CheckConstraint("phone ~ '^[0-9]{10,11}$'", name="phone_has_10_or_11_digits")
    )

    @validates("phone")
    def _keep_only_phone_digits(self, _key: str, phone: str | None) -> str | None:
        if phone is None:
            return None
        return validate_cellphone_or_landline(phone)

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

    postal_code: Mapped[str | None] = mapped_column(
        String(8), CheckConstraint("postal_code ~ '^[0-9]{8}$'", name="postal_code_has_8_digits")
    )
    location: Mapped[WKBElement | None] = mapped_column(
        Geography(geometry_type="POINT", srid=WGS84_SRID)
    )
    preferred_causes: Mapped[list[Cause]] = mapped_column(
        ARRAY(enum_type(Cause)), server_default=EMPTY_LIST
    )

    @validates("postal_code")
    def _validate_postal_code(self, _key: str, postal_code: str | None) -> str | None:
        if postal_code is None:
            return None
        return normalize_cep(postal_code)


class Manager(User):
    __mapper_args__ = {"polymorphic_identity": Role.MANAGER}

    institutions: Mapped[list["Institution"]] = relationship(back_populates="manager")
