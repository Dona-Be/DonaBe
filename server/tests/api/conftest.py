import pytest
from sqlalchemy.orm import Session

from src.models.user import Donor
from tests.api.helpers import create_donor


@pytest.fixture
def donor(db_session: Session) -> Donor:
    return create_donor(db_session)
