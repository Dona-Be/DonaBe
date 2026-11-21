from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from src.api.authentication import CurrentUser
from src.api.dependencies import NotificationServiceDep
from src.models.notification import Notification
from src.schemas.notification import PublicNotification, UnreadCount

router = APIRouter(prefix="/notifications", tags=["notifications"])

# PostgreSQL refuses a larger integer, which would turn into a 500.
MAX_INTEGER = 2**31 - 1


@router.get(
    "",
    response_model=list[PublicNotification],
    summary="List your notifications",
    description="Newest first, 20 per page.",
)
def list_notifications(
    user: CurrentUser,
    service: NotificationServiceDep,
    page: Annotated[int, Query(ge=1, le=MAX_INTEGER)] = 1,
    *,
    unread: bool = False,
) -> list[Notification]:
    return service.list_page(user, page, unread_only=unread)


@router.get("/unread-count", summary="Count your unread notifications")
def count_unread(user: CurrentUser, service: NotificationServiceDep) -> UnreadCount:
    return UnreadCount(count=service.count_unread(user))


@router.post(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark all your notifications as read",
)
def mark_all_as_read(user: CurrentUser, service: NotificationServiceDep) -> None:
    service.mark_all_as_read(user)


@router.post(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark one of your notifications as read",
)
def mark_as_read(
    notification_id: Annotated[int, Path(ge=1, le=MAX_INTEGER)],
    user: CurrentUser,
    service: NotificationServiceDep,
) -> None:
    service.mark_as_read(user, notification_id)
