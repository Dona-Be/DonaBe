from fastapi import status

from src.api.error_handlers import status_for
from src.domain.exceptions import UserAlreadyExistsError


class ConcurrentSignupError(UserAlreadyExistsError):
    pass


def test_a_subclass_of_a_mapped_error_gets_the_same_status() -> None:
    assert status_for(ConcurrentSignupError("maria@exemplo.com")) == status.HTTP_409_CONFLICT
