"""Business logic for notification creation and lifecycle management."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.notifications import (
    DEFAULT_MAX_DELIVERY_ATTEMPTS,
    DEFAULT_NOTIFICATION_CHANNEL,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    default_priority_for_type,
)
from backend.app.models.notification import Notification
from backend.app.models.user import User
from backend.app.repositories.notification_repository import (
    NotificationRepository,
)


class NotificationNotFoundError(LookupError):
    """Raised when a notification cannot be found."""


class NotificationPermissionError(PermissionError):
    """Raised when a user cannot operate on a notification."""


class NotificationValidationError(ValueError):
    """Raised when notification input violates business rules."""


class NotificationConflictError(RuntimeError):
    """Raised when a notification lifecycle action is invalid."""


class NotificationService:
    """Application service for notification operations."""

    def __init__(
        self,
        db: Session,
        repository: NotificationRepository | None = None,
    ) -> None:
        self.db = db
        self.repository = repository or NotificationRepository(db)

    def create_notification(
        self,
        *,
        recipient_user_id: int,
        notification_type: str,
        title: str,
        message: str,
        actor_user_id: int | None = None,
        priority: str | None = None,
        channel: str = DEFAULT_NOTIFICATION_CHANNEL,
        entity_type: str | None = None,
        entity_id: int | None = None,
        action_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        deduplication_key: str | None = None,
        expires_at: datetime | None = None,
        max_delivery_attempts: int = DEFAULT_MAX_DELIVERY_ATTEMPTS,
        auto_deliver_in_app: bool = True,
        commit: bool = True,
    ) -> Notification:
        recipient = self._get_active_user(recipient_user_id)

        if actor_user_id is not None:
            self._get_user(actor_user_id)

        normalized_type = self._validate_notification_type(notification_type)
        normalized_channel = self._validate_channel(channel)
        normalized_priority = self._validate_priority(
            priority or default_priority_for_type(normalized_type)
        )

        clean_title = title.strip()
        clean_message = message.strip()

        if not clean_title:
            raise NotificationValidationError(
                "Notification title cannot be empty."
            )

        if not clean_message:
            raise NotificationValidationError(
                "Notification message cannot be empty."
            )

        if len(clean_title) > 255:
            raise NotificationValidationError(
                "Notification title cannot exceed 255 characters."
            )

        if entity_id is not None and entity_id <= 0:
            raise NotificationValidationError(
                "Entity ID must be greater than zero."
            )

        if max_delivery_attempts <= 0:
            raise NotificationValidationError(
                "Maximum delivery attempts must be greater than zero."
            )

        normalized_expiry = self._normalize_datetime(expires_at)

        if (
            normalized_expiry is not None
            and normalized_expiry <= self._utc_now()
        ):
            raise NotificationValidationError(
                "Notification expiry must be in the future."
            )

        resolved_deduplication_key = (
            deduplication_key.strip()
            if deduplication_key and deduplication_key.strip()
            else self.generate_deduplication_key(
                recipient_user_id=recipient_user_id,
                notification_type=normalized_type,
                entity_type=entity_type,
                entity_id=entity_id,
                title=clean_title,
            )
        )

        existing = self.repository.get_by_deduplication_key(
            recipient_user_id,
            resolved_deduplication_key,
        )

        if existing is not None:
            return self._refresh_duplicate(
                existing,
                title=clean_title,
                message=clean_message,
                priority=normalized_priority,
                actor_user_id=actor_user_id,
                action_url=action_url,
                metadata=metadata,
                expires_at=normalized_expiry,
                auto_deliver_in_app=auto_deliver_in_app,
                commit=commit,
            )

        now = self._utc_now()

        notification = Notification(
            recipient_user_id=recipient.id,
            actor_user_id=actor_user_id,
            notification_type=normalized_type,
            priority=normalized_priority,
            channel=normalized_channel,
            status=NotificationStatus.PENDING.value,
            title=clean_title,
            message=clean_message,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            metadata_json=metadata,
            deduplication_key=resolved_deduplication_key,
            max_delivery_attempts=max_delivery_attempts,
            expires_at=normalized_expiry,
        )

        if (
            auto_deliver_in_app
            and normalized_channel == NotificationChannel.IN_APP.value
        ):
            notification.status = NotificationStatus.DELIVERED.value
            notification.delivered_at = now

        try:
            self.repository.create(notification)

            if commit:
                self.db.commit()
                self.db.refresh(notification)

            return notification

        except IntegrityError as exc:
            self.db.rollback()

            duplicate = self.repository.get_by_deduplication_key(
                recipient_user_id,
                resolved_deduplication_key,
            )

            if duplicate is not None:
                return duplicate

            raise NotificationConflictError(
                "Unable to create notification due to a database conflict."
            ) from exc

    def create_bulk_notifications(
        self,
        *,
        recipient_user_ids: Iterable[int],
        notification_type: str,
        title: str,
        message: str,
        actor_user_id: int | None = None,
        priority: str | None = None,
        channel: str = DEFAULT_NOTIFICATION_CHANNEL,
        entity_type: str | None = None,
        entity_id: int | None = None,
        action_url: str | None = None,
        metadata: dict[str, Any] | None = None,
        expires_at: datetime | None = None,
    ) -> list[Notification]:
        unique_recipient_ids = list(dict.fromkeys(recipient_user_ids))

        if not unique_recipient_ids:
            raise NotificationValidationError(
                "At least one recipient is required."
            )

        notifications: list[Notification] = []

        try:
            for recipient_user_id in unique_recipient_ids:
                notification = self.create_notification(
                    recipient_user_id=recipient_user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    actor_user_id=actor_user_id,
                    priority=priority,
                    channel=channel,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action_url=action_url,
                    metadata=metadata,
                    expires_at=expires_at,
                    commit=False,
                )
                notifications.append(notification)

            self.db.commit()

            for notification in notifications:
                self.db.refresh(notification)

            return notifications

        except Exception:
            self.db.rollback()
            raise

    def get_notification(
        self,
        *,
        notification_id: int,
        recipient_user_id: int | None = None,
        include_deleted: bool = False,
    ) -> Notification:
        if recipient_user_id is None:
            notification = self.repository.get_by_id(
                notification_id,
                include_deleted=include_deleted,
            )
        else:
            notification = self.repository.get_for_recipient(
                notification_id,
                recipient_user_id,
                include_deleted=include_deleted,
            )

        if notification is None:
            raise NotificationNotFoundError(
                f"Notification {notification_id} was not found."
            )

        return notification

    def list_notifications(
        self,
        *,
        recipient_user_id: int,
        notification_type: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        channel: str | None = None,
        is_read: bool | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        include_deleted: bool = False,
        include_expired: bool = False,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        self._get_user(recipient_user_id)

        if limit < 1 or limit > 100:
            raise NotificationValidationError(
                "Limit must be between 1 and 100."
            )

        if offset < 0:
            raise NotificationValidationError("Offset cannot be negative.")

        records = list(
            self.repository.list_for_recipient(
                recipient_user_id,
                notification_type=notification_type,
                priority=priority,
                status=status,
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
        )

        total = self.repository.count_for_recipient(
            recipient_user_id,
            notification_type=notification_type,
            priority=priority,
            status=status,
            channel=channel,
            is_read=is_read,
            entity_type=entity_type,
            entity_id=entity_id,
            created_from=created_from,
            created_to=created_to,
            include_deleted=include_deleted,
            include_expired=include_expired,
        )

        return records, total

    def mark_as_read(
        self,
        *,
        notification_id: int,
        recipient_user_id: int,
    ) -> Notification:
        notification = self.get_notification(
            notification_id=notification_id,
            recipient_user_id=recipient_user_id,
        )

        if notification.is_deleted:
            raise NotificationConflictError(
                "A deleted notification cannot be marked as read."
            )

        if notification.is_read:
            return notification

        notification.is_read = True
        notification.read_at = self._utc_now()

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def mark_as_unread(
        self,
        *,
        notification_id: int,
        recipient_user_id: int,
    ) -> Notification:
        notification = self.get_notification(
            notification_id=notification_id,
            recipient_user_id=recipient_user_id,
        )

        if notification.is_deleted:
            raise NotificationConflictError(
                "A deleted notification cannot be marked as unread."
            )

        notification.is_read = False
        notification.read_at = None

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def mark_all_as_read(self, *, recipient_user_id: int) -> int:
        self._get_user(recipient_user_id)

        count = self.repository.bulk_mark_read(
            recipient_user_id,
            read_at=self._utc_now(),
        )

        self.db.commit()
        return count

    def mark_many_as_read(
        self,
        *,
        recipient_user_id: int,
        notification_ids: list[int],
    ) -> int:
        if not notification_ids:
            return 0

        count = self.repository.bulk_mark_read(
            recipient_user_id,
            notification_ids=list(dict.fromkeys(notification_ids)),
            read_at=self._utc_now(),
        )

        self.db.commit()
        return count

    def mark_delivered(
        self,
        *,
        notification_id: int,
    ) -> Notification:
        notification = self.get_notification(notification_id=notification_id)

        if notification.is_deleted:
            raise NotificationConflictError(
                "A deleted notification cannot be delivered."
            )

        if notification.status == NotificationStatus.CANCELLED.value:
            raise NotificationConflictError(
                "A cancelled notification cannot be delivered."
            )

        notification.status = NotificationStatus.DELIVERED.value
        notification.delivered_at = self._utc_now()
        notification.failed_at = None
        notification.failure_reason = None
        notification.next_retry_at = None

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def mark_failed(
        self,
        *,
        notification_id: int,
        failure_reason: str,
    ) -> Notification:
        notification = self.get_notification(notification_id=notification_id)

        if notification.is_deleted:
            raise NotificationConflictError(
                "A deleted notification cannot fail delivery."
            )

        reason = failure_reason.strip()

        if not reason:
            raise NotificationValidationError(
                "Failure reason cannot be empty."
            )

        now = self._utc_now()
        notification.delivery_attempts += 1
        notification.failed_at = now
        notification.failure_reason = reason
        notification.delivered_at = None

        if (
            notification.delivery_attempts
            >= notification.max_delivery_attempts
        ):
            notification.status = NotificationStatus.FAILED.value
            notification.next_retry_at = None
        else:
            notification.status = NotificationStatus.FAILED.value
            notification.next_retry_at = now + self._retry_delay(
                notification.delivery_attempts
            )

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def retry_notification(
        self,
        *,
        notification_id: int,
    ) -> Notification:
        notification = self.get_notification(notification_id=notification_id)

        if notification.is_deleted:
            raise NotificationConflictError(
                "A deleted notification cannot be retried."
            )

        if notification.status == NotificationStatus.DELIVERED.value:
            raise NotificationConflictError(
                "A delivered notification cannot be retried."
            )

        if notification.status == NotificationStatus.CANCELLED.value:
            raise NotificationConflictError(
                "A cancelled notification cannot be retried."
            )

        if (
            notification.delivery_attempts
            >= notification.max_delivery_attempts
        ):
            raise NotificationConflictError(
                "Maximum delivery attempts have been reached."
            )

        notification.status = NotificationStatus.PENDING.value
        notification.next_retry_at = None
        notification.failed_at = None
        notification.failure_reason = None

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def cancel_notification(
        self,
        *,
        notification_id: int,
    ) -> Notification:
        notification = self.get_notification(notification_id=notification_id)

        if notification.status == NotificationStatus.DELIVERED.value:
            raise NotificationConflictError(
                "A delivered notification cannot be cancelled."
            )

        notification.status = NotificationStatus.CANCELLED.value
        notification.next_retry_at = None

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def delete_notification(
        self,
        *,
        notification_id: int,
        recipient_user_id: int,
        deleted_by_user_id: int,
    ) -> Notification:
        notification = self.get_notification(
            notification_id=notification_id,
            recipient_user_id=recipient_user_id,
        )

        self._get_user(deleted_by_user_id)

        if notification.is_deleted:
            return notification

        notification.is_deleted = True
        notification.deleted_at = self._utc_now()
        notification.deleted_by_user_id = deleted_by_user_id

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def restore_notification(
        self,
        *,
        notification_id: int,
        recipient_user_id: int,
    ) -> Notification:
        notification = self.get_notification(
            notification_id=notification_id,
            recipient_user_id=recipient_user_id,
            include_deleted=True,
        )

        if not notification.is_deleted:
            return notification

        notification.is_deleted = False
        notification.deleted_at = None
        notification.deleted_by_user_id = None

        self.db.commit()
        self.db.refresh(notification)

        return notification

    def delete_many(
        self,
        *,
        recipient_user_id: int,
        notification_ids: list[int],
        deleted_by_user_id: int,
    ) -> int:
        self._get_user(deleted_by_user_id)

        count = self.repository.bulk_soft_delete(
            recipient_user_id,
            list(dict.fromkeys(notification_ids)),
            deleted_at=self._utc_now(),
            deleted_by_user_id=deleted_by_user_id,
        )

        self.db.commit()
        return count

    def restore_many(
        self,
        *,
        recipient_user_id: int,
        notification_ids: list[int],
    ) -> int:
        count = self.repository.bulk_restore(
            recipient_user_id,
            list(dict.fromkeys(notification_ids)),
        )

        self.db.commit()
        return count

    def get_unread_count(self, *, recipient_user_id: int) -> int:
        return self.repository.count_unread(recipient_user_id)

    def get_statistics(
        self,
        *,
        recipient_user_id: int,
    ) -> dict[str, int]:
        return self.repository.get_statistics(recipient_user_id)

    def get_retry_queue(
        self,
        *,
        limit: int = 100,
    ) -> list[Notification]:
        return list(self.repository.list_retryable(limit=limit))

    def cleanup_expired_notifications(
        self,
        *,
        limit: int = 100,
    ) -> int:
        count = self.repository.soft_delete_expired(
            deleted_at=self._utc_now(),
            limit=limit,
        )

        self.db.commit()
        return count

    @staticmethod
    def generate_deduplication_key(
        *,
        recipient_user_id: int,
        notification_type: str,
        entity_type: str | None,
        entity_id: int | None,
        title: str,
    ) -> str:
        source = "|".join(
            [
                str(recipient_user_id),
                notification_type.strip().lower(),
                (entity_type or "none").strip().lower(),
                str(entity_id or 0),
                title.strip().lower(),
            ]
        )

        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        return f"notification:{digest}"

    def _refresh_duplicate(
        self,
        notification: Notification,
        *,
        title: str,
        message: str,
        priority: str,
        actor_user_id: int | None,
        action_url: str | None,
        metadata: dict[str, Any] | None,
        expires_at: datetime | None,
        auto_deliver_in_app: bool,
        commit: bool,
    ) -> Notification:
        notification.title = title
        notification.message = message
        notification.priority = priority
        notification.actor_user_id = actor_user_id
        notification.action_url = action_url
        notification.metadata_json = metadata
        notification.expires_at = expires_at

        if notification.is_deleted:
            notification.is_deleted = False
            notification.deleted_at = None
            notification.deleted_by_user_id = None

        if (
            auto_deliver_in_app
            and notification.channel == NotificationChannel.IN_APP.value
        ):
            notification.status = NotificationStatus.DELIVERED.value
            notification.delivered_at = self._utc_now()
            notification.failure_reason = None
            notification.failed_at = None
            notification.next_retry_at = None

        if commit:
            self.db.commit()
            self.db.refresh(notification)
        else:
            self.db.flush()

        return notification

    def _get_user(self, user_id: int) -> User:
        user = self.db.scalar(select(User).where(User.id == user_id))

        if user is None:
            raise NotificationValidationError(
                f"User {user_id} does not exist."
            )

        return user

    def _get_active_user(self, user_id: int) -> User:
        user = self._get_user(user_id)

        if hasattr(user, "is_active") and not user.is_active:
            raise NotificationValidationError(
                f"User {user_id} is inactive."
            )

        if hasattr(user, "is_deleted") and user.is_deleted:
            raise NotificationValidationError(
                f"User {user_id} is deleted."
            )

        return user

    @staticmethod
    def _validate_notification_type(value: str) -> str:
        normalized = value.strip().lower()
        supported = {item.value for item in NotificationType}

        if normalized not in supported:
            raise NotificationValidationError(
                f"Unsupported notification type: {value}."
            )

        return normalized

    @staticmethod
    def _validate_priority(value: str) -> str:
        normalized = value.strip().lower()
        supported = {item.value for item in NotificationPriority}

        if normalized not in supported:
            raise NotificationValidationError(
                f"Unsupported notification priority: {value}."
            )

        return normalized

    @staticmethod
    def _validate_channel(value: str) -> str:
        normalized = value.strip().lower()
        supported = {item.value for item in NotificationChannel}

        if normalized not in supported:
            raise NotificationValidationError(
                f"Unsupported notification channel: {value}."
            )

        return normalized

    @staticmethod
    def _retry_delay(attempt_number: int) -> timedelta:
        minutes = min(2 ** max(attempt_number - 1, 0), 60)
        return timedelta(minutes=minutes)

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)
