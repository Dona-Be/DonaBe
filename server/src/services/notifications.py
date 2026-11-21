from datetime import UTC, datetime

from src.domain.exceptions import NotificationNotFoundError
from src.models.notification import Notification
from src.models.user import User
from src.repositories.notifications import NotificationRepository

PAGE_SIZE = 20


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self._repository = repository

    def list_page(self, user: User, page: int, *, unread_only: bool) -> list[Notification]:
        return self._repository.list_by_recipient(
            user.id, unread_only=unread_only, limit=PAGE_SIZE, offset=(page - 1) * PAGE_SIZE
        )

    def count_unread(self, user: User) -> int:
        return self._repository.count_unread(user.id)

    def mark_as_read(self, user: User, notification_id: int) -> None:
        notification = self._repository.find_by_id(notification_id)
        if notification is None or notification.recipient_id != user.id:
            raise NotificationNotFoundError()
        if notification.read_at is None:
            notification.read_at = datetime.now(UTC)
            self._repository.save(notification)

    def mark_all_as_read(self, user: User) -> None:
        self._repository.mark_all_as_read(user.id, datetime.now(UTC))
