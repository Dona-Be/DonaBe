from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfile:
    email: str
    name: str
    picture_url: str | None
