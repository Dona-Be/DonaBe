from datetime import datetime
from typing import Annotated

from pydantic import ConfigDict, Field

from src.domain.enums import NeedStatus
from src.schemas.text import StrictText

MAX_NEED_TEXT_LENGTH = 200
MAX_NEED_DESCRIPTION_LENGTH = 2000

NeedTitle = Annotated[str, Field(pattern=r"\S", max_length=MAX_NEED_TEXT_LENGTH)]
NeedDescription = Annotated[str, Field(pattern=r"\S", max_length=MAX_NEED_DESCRIPTION_LENGTH)]
NeedQuantity = Annotated[str, Field(max_length=MAX_NEED_TEXT_LENGTH)]


class NeedChanges(StrictText):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: NeedTitle | None = None
    description: NeedDescription | None = None
    quantity: NeedQuantity | None = None


class NewNeed(NeedChanges):
    title: NeedTitle
    description: NeedDescription
    quantity: NeedQuantity | None = None


class PublicNeed(StrictText):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    quantity: str | None
    status: NeedStatus
    closed_at: datetime | None
