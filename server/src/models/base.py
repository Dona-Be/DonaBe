from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, MetaData, func
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column

ENUM_VALUE_LENGTH = 30

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def enum_values(enum: type[StrEnum]) -> list[str]:
    return [member.value for member in enum]


def enum_type(enum: type[StrEnum]) -> Enum:
    # Stored as varchar instead of a native PostgreSQL enum so adding a value needs no ALTER TYPE.
    return Enum(enum, native_enum=False, length=ENUM_VALUE_LENGTH, values_callable=enum_values)


def created_at_column() -> MappedColumn[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())
