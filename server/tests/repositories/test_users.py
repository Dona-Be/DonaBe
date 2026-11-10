import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.exceptions import UserAlreadyExistsError
from src.domain.user_profile import UserProfile
from src.models.user import Donor, Manager
from src.repositories.users import SqlAlchemyUserRepository
from tests.fakes import USER_EMAIL, USER_NAME

PROFILE = UserProfile(email=USER_EMAIL, name=USER_NAME, picture_url=None)


def test_saving_a_second_user_with_the_same_email_is_a_registration_conflict(
    db_session: Session,
) -> None:
    repository = SqlAlchemyUserRepository(db_session)
    repository.save(Donor.from_profile(PROFILE))
    manager = Manager.from_profile(PROFILE)

    with pytest.raises(UserAlreadyExistsError, match=USER_EMAIL):
        repository.save(manager)

    assert isinstance(repository.find_by_email(USER_EMAIL), Donor)


def test_a_new_donor_starts_without_preferred_causes(db_session: Session) -> None:
    donor = Donor.from_profile(PROFILE)

    SqlAlchemyUserRepository(db_session).save(donor)

    assert donor.preferred_causes == []


@pytest.mark.parametrize(
    ("column", "value", "constraint"),
    [
        ("phone", "11 98765432", "ck_users_phone_has_10_or_11_digits"),
        ("postal_code", "01310-20", "ck_users_postal_code_has_8_digits"),
    ],
)
def test_the_database_rejects_values_that_are_not_only_digits(
    db_session: Session, column: str, value: str, constraint: str
) -> None:
    SqlAlchemyUserRepository(db_session).save(Donor.from_profile(PROFILE))

    # A bulk UPDATE skips the model validators, so only the check constraint stands in the way.
    with pytest.raises(IntegrityError, match=constraint):
        db_session.execute(update(Donor).values({column: value}))
