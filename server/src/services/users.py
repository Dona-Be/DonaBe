from src.domain.enums import Role
from src.domain.exceptions import UserAlreadyRegistered
from src.domain.user_profile import UserProfile
from src.models.user import Donor, Manager, User
from src.repositories.users import UserRepository

USER_CLASS_BY_ROLE: dict[Role, type[User]] = {Role.DONOR: Donor, Role.MANAGER: Manager}


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def identify_on_login(self, profile: UserProfile) -> User | None:
        return self._repository.find_by_email(profile.email)

    def identify_session(self, user_id: int, session_version: int) -> User | None:
        user = self._repository.find_by_id(user_id)
        if user is None or user.session_version != session_version:
            return None
        return user

    def sign_up(self, profile: UserProfile, role: Role) -> User:
        if self._repository.find_by_email(profile.email) is not None:
            raise UserAlreadyRegistered(profile.email)
        user = USER_CLASS_BY_ROLE[role].from_profile(profile)
        self._repository.save(user)
        return user

    def logout(self, user: User) -> None:
        user.end_sessions()
        self._repository.save(user)
