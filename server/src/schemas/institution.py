from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.enums import Cause, InstitutionType, Verdict
from src.schemas.text import StrictText
from src.services.search_strategies import SearchResult

MAX_TEXT_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
STATE_FORMAT = r"^[A-Z]{2}$"
EMAIL_OR_EMPTY = r"^([^@\s]+@[^@\s]+\.[^@\s]+)?$"
LINK_OR_EMPTY = r"^(https?://\S+)?$"

Text = Annotated[str, Field(max_length=MAX_TEXT_LENGTH)]
NonBlankText = Annotated[str, Field(pattern=r"\S", max_length=MAX_TEXT_LENGTH)]
Email = Annotated[str, Field(pattern=EMAIL_OR_EMPTY, max_length=MAX_TEXT_LENGTH)]
Link = Annotated[str, Field(pattern=LINK_OR_EMPTY, max_length=MAX_TEXT_LENGTH)]


class InstitutionChanges(StrictText):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    trade_name: Text | None = None
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    causes: list[Cause] | None = Field(default=None, max_length=len(Cause))
    phone: str | None = None
    contact_email: Email | None = None
    website: Link | None = None
    instagram: Link | None = None
    facebook: Link | None = None
    street: NonBlankText | None = None
    number: NonBlankText | None = None
    complement: Text | None = None
    neighborhood: NonBlankText | None = None
    city: NonBlankText | None = None
    state: str | None = Field(default=None, pattern=STATE_FORMAT)
    postal_code: str | None = None

    @field_validator("causes")
    @classmethod
    def keep_each_cause_once(cls, causes: list[Cause] | None) -> list[Cause] | None:
        return None if causes is None else list(dict.fromkeys(causes))


class NewInstitution(InstitutionChanges):
    cnpj: str


class InstitutionPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: InstitutionType
    cnpj: str
    legal_name: str
    trade_name: str | None
    street: str | None
    number: str | None
    complement: str | None
    neighborhood: str | None
    city: str
    state: str
    postal_code: str | None
    verdict: Verdict
    reasons: list[str]


class PublicInstitution(InstitutionPreview):
    id: int
    description: str | None
    causes: list[Cause]
    phone: str | None
    contact_email: str | None
    website: str | None
    instagram: str | None
    facebook: str | None


class OpenNeed(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    quantity: str | None


class InstitutionPage(PublicInstitution):
    open_needs: list[OpenNeed]


class InstitutionSearchResult(BaseModel):
    id: int
    type: InstitutionType
    legal_name: str
    trade_name: str | None
    causes: list[Cause]
    verdict: Verdict
    distance_km: float
    score: int | None
    # Not "reasons": an institution already has reasons, the ones behind its CNPJ verdict.
    match_reasons: list[str]

    @classmethod
    def from_result(cls, result: SearchResult) -> Self:
        institution = result.institution
        return cls(
            id=institution.id,
            type=institution.type,
            legal_name=institution.legal_name,
            trade_name=institution.trade_name,
            causes=institution.causes,
            verdict=institution.verdict,
            distance_km=result.distance_km,
            score=result.score,
            match_reasons=list(result.reasons),
        )
