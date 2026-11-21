from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.models.notification import Notification


class NotificationRepository(ABC):
    @abstractmethod
    def save(self, notification: Notification) -> None: ...

    @abstractmethod
    def find_by_id(self, notification_id: int) -> Notification | None: ...

    @abstractmethod
    def list_by_recipient(
        self, recipient_id: int, *, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]: ...

    @abstractmethod
    def count_unread(self, recipient_id: int) -> int: ...

    @abstractmethod
    def mark_all_as_read(self, recipient_id: int, read_at: datetime) -> None: ...


class SqlAlchemyNotificationRepository(NotificationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, notification: Notification) -> None:
        self._session.add(notification)
        self._session.commit()

    def find_by_id(self, notification_id: int) -> Notification | None:
        return self._session.get(Notification, notification_id)

    def list_by_recipient(
        self, recipient_id: int, *, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]:
        query = select(Notification).where(Notification.recipient_id == recipient_id)
        if unread_only:
            query = query.where(Notification.read_at.is_(None))
        newest_first = query.order_by(Notification.created_at.desc(), Notification.id.desc())
        return list(self._session.scalars(newest_first.limit(limit).offset(offset)))

    def count_unread(self, recipient_id: int) -> int:
        unread = select(func.count(Notification.id)).where(
            Notification.recipient_id == recipient_id, Notification.read_at.is_(None)
        )
        return self._session.execute(unread).scalar_one()

    def mark_all_as_read(self, recipient_id: int, read_at: datetime) -> None:
        self._session.execute(
            update(Notification)
            .where(Notification.recipient_id == recipient_id, Notification.read_at.is_(None))
            .values(read_at=read_at)
        )
        self._session.commit()
