import pytest
from sqlalchemy.orm import Session

from src.domain.exceptions import InstitutionAlreadyExistsError
from src.repositories.institutions import SqlAlchemyInstitutionRepository
from tests.models.helpers import new_institution, save_need


def test_saving_a_second_institution_with_the_same_cnpj_is_a_registration_conflict(
    db_session: Session,
) -> None:
    saved = save_need(db_session).institution
    repository = SqlAlchemyInstitutionRepository(db_session)
    duplicate = new_institution(saved.manager)

    with pytest.raises(InstitutionAlreadyExistsError, match=saved.cnpj):
        repository.save(duplicate)

    assert repository.list_by_manager(saved.manager_id) == [saved]
