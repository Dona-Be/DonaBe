from datetime import datetime
from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import Cause, Verdict
from src.models.base import Base, created_at_column, enum_type

if TYPE_CHECKING:
    from src.models.user import Manager

WGS84_SRID = 4326
CAUSES_INDEX = "ix_institutions_causes"
EMPTY_LIST = "{}"


class Institution(Base):
    __tablename__ = "institutions"
    __table_args__ = (Index(CAUSES_INDEX, "causes", postgresql_using="gin"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True)
    legal_name: Mapped[str]
    trade_name: Mapped[str | None]
    description: Mapped[str | None]
    causes: Mapped[list[Cause]] = mapped_column(ARRAY(enum_type(Cause)), server_default=EMPTY_LIST)
    street: Mapped[str]
    number: Mapped[str]
    complement: Mapped[str | None]
    neighborhood: Mapped[str]
    city: Mapped[str]
    state: Mapped[str] = mapped_column(String(2))
    postal_code: Mapped[str] = mapped_column(String(8))
    location: Mapped[WKBElement | None] = mapped_column(
        Geography(geometry_type="POINT", srid=WGS84_SRID)
    )
    phone: Mapped[str | None]
    contact_email: Mapped[str | None]
    website: Mapped[str | None]
    instagram: Mapped[str | None]
    facebook: Mapped[str | None]
    pix_key: Mapped[str | None]
    verdict: Mapped[Verdict] = mapped_column(enum_type(Verdict))
    reasons: Mapped[list[str]] = mapped_column(ARRAY(String))
    cnpj_data: Mapped[dict[str, Any]] = mapped_column(JSONB, deferred=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = created_at_column()

    manager: Mapped["Manager"] = relationship(back_populates="institutions")
