import pytest
from sqlalchemy.orm import Session

from src.domain.exceptions import UserAlreadyRegistered
from src.domain.user_profile import UserProfile
from src.models.user import Donor, Manager
from src.repositories.users import SqlAlchemyUserRepository
from tests.fakes import USER_EMAIL, USER_NAME


def test_saving_a_second_user_with_the_same_email_is_a_registration_conflict(
    db_session: Session,
) -> None:
    repository = SqlAlchemyUserRepository(db_session)
    profile = UserProfile(email=USER_EMAIL, name=USER_NAME, picture_url=None)
    repository.save(Donor.from_profile(profile))

    with pytest.raises(UserAlreadyRegistered, match=USER_EMAIL):
        repository.save(Manager.from_profile(profile))

    assert isinstance(repository.find_by_email(USER_EMAIL), Donor)
