from abc import ABC, abstractmethod

from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.exceptions import UserAlreadyExistsError
from src.models.user import User


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def find_by_email(self, email: str) -> User | None: ...


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, user: User) -> None:
        self._session.add(user)
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            if not isinstance(error.orig, UniqueViolation):
                raise
            raise UserAlreadyExistsError(user.email) from error

    def find_by_id(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def find_by_email(self, email: str) -> User | None:
        return self._session.scalar(select(User).where(User.email == email))
