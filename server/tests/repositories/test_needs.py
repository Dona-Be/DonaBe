from sqlalchemy.orm import Session

from src.domain.enums import NeedStatus
from src.repositories.needs import SqlAlchemyNeedRepository
from tests.models.helpers import add_needs, new_institution, save_need


def test_counts_only_the_open_needs_of_the_institutions_asked_for(db_session: Session) -> None:
    # save_need leaves one open need in the first institution.
    first = save_need(db_session).institution
    add_needs(db_session, first, NeedStatus.OPEN, NeedStatus.FULFILLED, NeedStatus.CLOSED)
    without_open = new_institution(first.manager)
    without_open.cnpj = "00000000000001"
    add_needs(db_session, without_open, NeedStatus.FULFILLED)
    not_asked = new_institution(first.manager)
    not_asked.cnpj = "00000000000002"
    add_needs(db_session, not_asked, NeedStatus.OPEN)

    counts = SqlAlchemyNeedRepository(db_session).count_open_by_institution(
        [first.id, without_open.id]
    )

    assert counts == {first.id: 2}
