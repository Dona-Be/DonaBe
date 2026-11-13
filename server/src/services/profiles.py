from typing import Any

from geoalchemy2 import WKTElement

from src.domain.cep import normalize_cep
from src.domain.enums import Cause, Role
from src.domain.exceptions import FieldNotInProfileError
from src.domain.user_profile import UserProfile
from src.models.institution import WGS84_SRID
from src.models.user import User
from src.repositories.users import UserRepository
from src.services.locations import LocationService
from src.services.users import UserService


class ProfileService:
    def __init__(
        self, users: UserService, repository: UserRepository, locations: LocationService
    ) -> None:
        self._users = users
        self._repository = repository
        self._locations = locations

    def create_donor(
        self,
        profile: UserProfile,
        postal_code: str,
        preferred_causes: list[Cause],
        phone: str | None,
    ) -> User:
        return self._users.sign_up(
            profile,
            Role.DONOR,
            postal_code=postal_code,
            location=self._locate(postal_code),
            preferred_causes=preferred_causes,
            phone=phone,
        )

    def update(self, user: User, changes: dict[str, Any]) -> None:
        for field, value in changes.items():
            if not hasattr(user, field):
                raise FieldNotInProfileError(field)
            if field == "postal_code" and normalize_cep(value) != user.postal_code:
                user.location = self._locate(value)
            setattr(user, field, value)
        self._repository.save(user)

    def _locate(self, postal_code: str) -> WKTElement:
        coordinates = self._locations.locate(postal_code).coordinates
        return WKTElement(f"POINT({coordinates.longitude} {coordinates.latitude})", srid=WGS84_SRID)
