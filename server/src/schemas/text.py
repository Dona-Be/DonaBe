from pydantic import BaseModel, field_validator


class StrictText(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def reject_nul(cls, value: object) -> object:
        # PostgreSQL refuses a NUL in a text, which would turn into a 500.
        if isinstance(value, str) and "\x00" in value:
            raise ValueError("must not contain the NUL character")
        return value
