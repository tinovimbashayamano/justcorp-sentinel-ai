"""FastAPI routes for notification management."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_user
from backend.app.db.session import get_db
from backend.app.integrations.email.console_sender import (
    ConsoleEmailSender,
)
from backend.app.models.user import User
from backend.app.schemas.notification import (
    NotificationAdminCreateRequest,
    NotificationBulkOperationResponse,
    NotificationEmailRequest,
    NotificationIdsRequest,
    NotificationListResponse,
    NotificationResponse,
    NotificationRetryQueueResponse,
    NotificationStatisticsResponse,
    NotificationUnreadCountResponse,
)
from backend.app.services.notification_email_service import (
    NotificationEmailService,
)
from backend.app.services.notification_service import (
    NotificationConflictError,
    NotificationNotFoundError,
    NotificationService,
    NotificationValidationError,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


def get_notification_service(
    db: Session = Depends(get_db),
) -> NotificationService:
    """Construct a request-scoped notification service."""

    return NotificationService(db)


def get_notification_email_service(
    db: Session = Depends(get_db),
) -> NotificationEmailService:
    """Construct the development email notification service."""

    return NotificationEmailService(
        db,
        email_sender=ConsoleEmailSender(),
    )


def _user_id(user: User) -> int:
    value = getattr(user, "id", None)

    if value is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID is unavailable.",
        )

    return int(value)


def _role_name(user: User) -> str:
    role = getattr(user, "role", None)

    if role is None:
        return ""

    role_value = getattr(role, "value", role)
    return str(role_value).strip().lower()


def _require_privileged_user(user: User) -> None:
    allowed_roles = {
        "admin",
        "manager",
        "risk_manager",
    }

    if _role_name(user) not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this notification action.",
        )


def _translate_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, NotificationNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, NotificationValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    if isinstance(exc, NotificationConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Notification operation failed.",
    )


@router.get(
    "",
    response_model=NotificationListResponse,
)
def list_my_notifications(
    notification_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    notification_status: str | None = Query(
        default=None,
        alias="status",
    ),
    channel: str | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None, gt=0),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    include_expired: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    """List notifications belonging to the authenticated user."""

    try:
        notifications, total = service.list_notifications(
            recipient_user_id=_user_id(current_user),
            notification_type=notification_type,
            priority=priority,
            status=notification_status,
            channel=channel,
            is_read=is_read,
            entity_type=entity_type,
            entity_id=entity_id,
            created_from=created_from,
            created_to=created_to,
            include_deleted=include_deleted,
            include_expired=include_expired,
            limit=limit,
            offset=offset,
        )

        return NotificationListResponse(
            items=[
                NotificationResponse.model_validate(notification)
                for notification in notifications
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
)
def get_my_unread_count(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationUnreadCountResponse:
    """Return the authenticated user's unread-notification count."""

    return NotificationUnreadCountResponse(
        unread_count=service.get_unread_count(
            recipient_user_id=_user_id(current_user),
        )
    )


@router.get(
    "/statistics",
    response_model=NotificationStatisticsResponse,
)
def get_my_notification_statistics(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationStatisticsResponse:
    """Return notification statistics for the authenticated user."""

    statistics = service.get_statistics(
        recipient_user_id=_user_id(current_user)
    )

    return NotificationStatisticsResponse(**statistics)


@router.patch(
    "/read-all",
    response_model=NotificationBulkOperationResponse,
)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationBulkOperationResponse:
    """Mark all active notifications belonging to the user as read."""

    affected = service.mark_all_as_read(
        recipient_user_id=_user_id(current_user)
    )

    return NotificationBulkOperationResponse(affected_count=affected)


@router.patch(
    "/read-many",
    response_model=NotificationBulkOperationResponse,
)
def mark_many_notifications_read(
    payload: NotificationIdsRequest,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationBulkOperationResponse:
    """Mark selected owned notifications as read."""

    affected = service.mark_many_as_read(
        recipient_user_id=_user_id(current_user),
        notification_ids=payload.notification_ids,
    )

    return NotificationBulkOperationResponse(affected_count=affected)


@router.post(
    "/delete-many",
    response_model=NotificationBulkOperationResponse,
)
def delete_many_notifications(
    payload: NotificationIdsRequest,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationBulkOperationResponse:
    """Soft-delete selected owned notifications."""

    user_id = _user_id(current_user)

    affected = service.delete_many(
        recipient_user_id=user_id,
        notification_ids=payload.notification_ids,
        deleted_by_user_id=user_id,
    )

    return NotificationBulkOperationResponse(affected_count=affected)


@router.post(
    "/restore-many",
    response_model=NotificationBulkOperationResponse,
)
def restore_many_notifications(
    payload: NotificationIdsRequest,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationBulkOperationResponse:
    """Restore selected owned notifications."""

    affected = service.restore_many(
        recipient_user_id=_user_id(current_user),
        notification_ids=payload.notification_ids,
    )

    return NotificationBulkOperationResponse(affected_count=affected)


@router.post(
    "/admin",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_administrative_notification(
    payload: NotificationAdminCreateRequest,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Create a notification for another user."""

    _require_privileged_user(current_user)

    try:
        notification = service.create_notification(
            recipient_user_id=payload.recipient_user_id,
            actor_user_id=payload.actor_user_id or _user_id(current_user),
            notification_type=payload.notification_type,
            priority=payload.priority,
            channel=payload.channel,
            title=payload.title,
            message=payload.message,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            action_url=payload.action_url,
            metadata=payload.metadata,
            deduplication_key=payload.deduplication_key,
            expires_at=payload.expires_at,
            max_delivery_attempts=payload.max_delivery_attempts,
        )

        return NotificationResponse.model_validate(notification)

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.post(
    "/admin/email",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_and_deliver_email_notification(
    payload: NotificationEmailRequest,
    current_user: User = Depends(get_current_active_user),
    email_service: NotificationEmailService = Depends(
        get_notification_email_service
    ),
) -> NotificationResponse:
    """Create and deliver an email notification."""

    _require_privileged_user(current_user)

    try:
        notification = (
            email_service.create_and_deliver_email_notification(
                recipient_user_id=payload.recipient_user_id,
                actor_user_id=payload.actor_user_id
                or _user_id(current_user),
                title=payload.title,
                message=payload.message,
                priority=payload.priority,
                entity_type=payload.entity_type,
                entity_id=payload.entity_id,
                action_url=payload.action_url,
                metadata=payload.metadata,
                deduplication_key=payload.deduplication_key,
            )
        )

        return NotificationResponse.model_validate(notification)

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.post(
    "/admin/process-email-retries",
    response_model=NotificationRetryQueueResponse,
)
def process_email_retry_queue(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    email_service: NotificationEmailService = Depends(
        get_notification_email_service
    ),
) -> NotificationRetryQueueResponse:
    """Process retryable email notifications."""

    _require_privileged_user(current_user)

    try:
        result = email_service.process_retry_queue(limit=limit)

        return NotificationRetryQueueResponse(
            examined=result.examined,
            delivered=result.delivered,
            failed=result.failed,
            skipped=result.skipped,
        )

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.post(
    "/admin/cleanup-expired",
    response_model=NotificationBulkOperationResponse,
)
def cleanup_expired_notifications(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationBulkOperationResponse:
    """Soft-delete expired notifications."""

    _require_privileged_user(current_user)

    affected = service.cleanup_expired_notifications(limit=limit)

    return NotificationBulkOperationResponse(affected_count=affected)


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_my_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Retrieve one notification owned by the authenticated user."""

    try:
        notification = service.get_notification(
            notification_id=notification_id,
            recipient_user_id=_user_id(current_user),
        )

        return NotificationResponse.model_validate(notification)

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Mark one owned notification as read."""

    try:
        notification = service.mark_as_read(
            notification_id=notification_id,
            recipient_user_id=_user_id(current_user),
        )

        return NotificationResponse.model_validate(notification)

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.patch(
    "/{notification_id}/unread",
    response_model=NotificationResponse,
)
def mark_notification_unread(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Mark one owned notification as unread."""

    try:
        notification = service.mark_as_unread(
            notification_id=notification_id,
            recipient_user_id=_user_id(current_user),
        )

        return NotificationResponse.model_validate(notification)

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.delete(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def delete_my_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Soft-delete one owned notification."""

    try:
        user_id = _user_id(current_user)

        notification = service.delete_notification(
            notification_id=notification_id,
            recipient_user_id=user_id,
            deleted_by_user_id=user_id,
        )

        return NotificationResponse.model_validate(notification)

    except Exception as exc:
        raise _translate_service_error(exc) from exc


@router.post(
    "/{notification_id}/restore",
    response_model=NotificationResponse,
)
def restore_my_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Restore one owned soft-deleted notification."""

    try:
        notification = service.restore_notification(
            notification_id=notification_id,
            recipient_user_id=_user_id(current_user),
        )

        return NotificationResponse.model_validate(notification)

    except Exception as exc:
        raise _translate_service_error(exc) from exc
