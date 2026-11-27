from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from src.domain.enums import NeedStatus
from src.models.institution import Institution
from src.models.need import Need
from src.repositories.needs import SqlAlchemyNeedRepository
from tests.models.helpers import new_institution, save_need


def add_needs(db_session: Session, institution: Institution, *statuses: NeedStatus) -> None:
    for status in statuses:
        db_session.add(
            Need(institution=institution, title="Cobertores", description="Doação", status=status)
        )
    db_session.commit()


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


def test_an_empty_page_does_not_query_the_database(db_session: Session) -> None:
    queries: list[Any] = []
    event.listen(db_session, "do_orm_execute", queries.append)

    counts = SqlAlchemyNeedRepository(db_session).count_open_by_institution([])

    assert counts == {}
    assert queries == []
