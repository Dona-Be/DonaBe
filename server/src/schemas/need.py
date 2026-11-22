from datetime import datetime
from typing import Annotated

from pydantic import ConfigDict, Field

from src.domain.enums import NeedStatus
from src.schemas.institution import MAX_DESCRIPTION_LENGTH, NonBlankText, OpenNeed, Text
from src.schemas.text import StrictText

NeedDescription = Annotated[str, Field(pattern=r"\S", max_length=MAX_DESCRIPTION_LENGTH)]


class NeedChanges(StrictText):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: NonBlankText | None = None
    description: NeedDescription | None = None
    quantity: Text | None = None


class NewNeed(NeedChanges):
    title: NonBlankText
    description: NeedDescription


class PublicNeed(OpenNeed):
    status: NeedStatus
    closed_at: datetime | None
