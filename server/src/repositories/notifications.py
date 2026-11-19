from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.models.notification import Notification


class NotificationRepository(ABC):
    @abstractmethod
    def save(self, notification: Notification) -> None: ...


class SqlAlchemyNotificationRepository(NotificationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, notification: Notification) -> None:
        self._session.add(notification)
        self._session.commit()
