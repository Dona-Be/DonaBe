import pytest
from sqlalchemy.orm import Session

from src.models.need import Need
from src.models.user import Donor
from tests.models.helpers import save_donor, save_need


@pytest.fixture
def need(db_session: Session) -> Need:
    return save_need(db_session)


@pytest.fixture
def donor(db_session: Session) -> Donor:
    return save_donor(db_session)
