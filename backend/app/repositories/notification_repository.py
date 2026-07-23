"""Database access layer for notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.orm import Session

from backend.app.models.notification import Notification


class NotificationRepository:
    """Provides persistence and query operations for notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        self.db.refresh(notification)
        return notification

    def get_by_id(
        self,
        notification_id: int,
        *,
        include_deleted: bool = False,
    ) -> Notification | None:
        query = select(Notification).where(Notification.id == notification_id)

        if not include_deleted:
            query = query.where(Notification.is_deleted.is_(False))

        return self.db.scalar(query)

    def get_for_recipient(
        self,
        notification_id: int,
        recipient_user_id: int,
        *,
        include_deleted: bool = False,
    ) -> Notification | None:
        query = select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_user_id == recipient_user_id,
        )

        if not include_deleted:
            query = query.where(Notification.is_deleted.is_(False))

        return self.db.scalar(query)

    def get_by_deduplication_key(
        self,
        recipient_user_id: int,
        deduplication_key: str,
        *,
        include_deleted: bool = False,
    ) -> Notification | None:
        query = select(Notification).where(
            Notification.recipient_user_id == recipient_user_id,
            Notification.deduplication_key == deduplication_key,
        )

        if not include_deleted:
            query = query.where(Notification.is_deleted.is_(False))

        return self.db.scalar(query)

    def list_for_recipient(
        self,
        recipient_user_id: int,
        *,
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
    ) -> Sequence[Notification]:
        query = self._recipient_query(
            recipient_user_id=recipient_user_id,
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

        query = (
            query.order_by(
                Notification.created_at.desc(),
                Notification.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return self.db.scalars(query).all()

    def count_for_recipient(
        self,
        recipient_user_id: int,
        *,
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
    ) -> int:
        filters = self._recipient_filters(
            recipient_user_id=recipient_user_id,
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

        query = select(func.count(Notification.id)).where(*filters)
        return int(self.db.scalar(query) or 0)

    def count_unread(self, recipient_user_id: int) -> int:
        query = select(func.count(Notification.id)).where(
            Notification.recipient_user_id == recipient_user_id,
            Notification.is_read.is_(False),
            Notification.is_deleted.is_(False),
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > func.now(),
            ),
        )

        return int(self.db.scalar(query) or 0)

    def get_statistics(self, recipient_user_id: int) -> dict[str, int]:
        query = select(
            func.count(Notification.id).label("total"),
            func.count(Notification.id)
            .filter(Notification.is_read.is_(False))
            .label("unread"),
            func.count(Notification.id)
            .filter(Notification.priority == "critical")
            .label("critical"),
            func.count(Notification.id)
            .filter(Notification.status == "pending")
            .label("pending"),
            func.count(Notification.id)
            .filter(Notification.status == "failed")
            .label("failed"),
            func.count(Notification.id)
            .filter(func.date(Notification.created_at) == func.current_date())
            .label("today"),
        ).where(
            Notification.recipient_user_id == recipient_user_id,
            Notification.is_deleted.is_(False),
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > func.now(),
            ),
        )

        row = self.db.execute(query).one()

        return {
            "total": int(row.total or 0),
            "unread": int(row.unread or 0),
            "critical": int(row.critical or 0),
            "pending": int(row.pending or 0),
            "failed": int(row.failed or 0),
            "today": int(row.today or 0),
        }

    def list_retryable(
        self,
        *,
        limit: int = 100,
        now: datetime | None = None,
    ) -> Sequence[Notification]:
        current_time = now or datetime.now().astimezone()

        query = (
            select(Notification)
            .where(
                Notification.is_deleted.is_(False),
                Notification.status.in_(("pending", "failed")),
                Notification.delivery_attempts
                < Notification.max_delivery_attempts,
                or_(
                    Notification.next_retry_at.is_(None),
                    Notification.next_retry_at <= current_time,
                ),
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > current_time,
                ),
            )
            .order_by(
                Notification.priority.desc(),
                Notification.next_retry_at.asc().nullsfirst(),
                Notification.created_at.asc(),
            )
            .limit(limit)
        )

        return self.db.scalars(query).all()

    def list_expired(
        self,
        *,
        limit: int = 100,
        now: datetime | None = None,
    ) -> Sequence[Notification]:
        current_time = now or datetime.now().astimezone()

        query = (
            select(Notification)
            .where(
                Notification.is_deleted.is_(False),
                Notification.expires_at.is_not(None),
                Notification.expires_at <= current_time,
            )
            .order_by(Notification.expires_at.asc())
            .limit(limit)
        )

        return self.db.scalars(query).all()

    def bulk_mark_read(
        self,
        recipient_user_id: int,
        *,
        notification_ids: list[int] | None = None,
        read_at: datetime,
    ) -> int:
        filters: list[Any] = [
            Notification.recipient_user_id == recipient_user_id,
            Notification.is_deleted.is_(False),
            Notification.is_read.is_(False),
        ]

        if notification_ids:
            filters.append(Notification.id.in_(notification_ids))

        statement = (
            update(Notification)
            .where(*filters)
            .values(
                is_read=True,
                read_at=read_at,
                updated_at=func.now(),
            )
        )

        result = self.db.execute(statement)
        return int(result.rowcount or 0)

    def bulk_soft_delete(
        self,
        recipient_user_id: int,
        notification_ids: list[int],
        *,
        deleted_at: datetime,
        deleted_by_user_id: int,
    ) -> int:
        if not notification_ids:
            return 0

        statement = (
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.recipient_user_id == recipient_user_id,
                Notification.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                deleted_at=deleted_at,
                deleted_by_user_id=deleted_by_user_id,
                updated_at=func.now(),
            )
        )

        result = self.db.execute(statement)
        return int(result.rowcount or 0)

    def bulk_restore(
        self,
        recipient_user_id: int,
        notification_ids: list[int],
    ) -> int:
        if not notification_ids:
            return 0

        statement = (
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.recipient_user_id == recipient_user_id,
                Notification.is_deleted.is_(True),
            )
            .values(
                is_deleted=False,
                deleted_at=None,
                deleted_by_user_id=None,
                updated_at=func.now(),
            )
        )

        result = self.db.execute(statement)
        return int(result.rowcount or 0)

    def soft_delete_expired(
        self,
        *,
        deleted_at: datetime,
        limit: int = 100,
    ) -> int:
        expired_ids = [
            notification.id
            for notification in self.list_expired(
                limit=limit,
                now=deleted_at,
            )
        ]

        if not expired_ids:
            return 0

        statement = (
            update(Notification)
            .where(Notification.id.in_(expired_ids))
            .values(
                is_deleted=True,
                deleted_at=deleted_at,
                status="cancelled",
                updated_at=func.now(),
            )
        )

        result = self.db.execute(statement)
        return int(result.rowcount or 0)

    def _recipient_query(
        self,
        **kwargs: Any,
    ) -> Select[tuple[Notification]]:
        filters = self._recipient_filters(**kwargs)
        return select(Notification).where(*filters)

    def _recipient_filters(
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
    ) -> list[Any]:
        filters: list[Any] = [
            Notification.recipient_user_id == recipient_user_id,
        ]

        if not include_deleted:
            filters.append(Notification.is_deleted.is_(False))

        if not include_expired:
            filters.append(
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > func.now(),
                )
            )

        if notification_type is not None:
            filters.append(
                Notification.notification_type == notification_type
            )

        if priority is not None:
            filters.append(Notification.priority == priority)

        if status is not None:
            filters.append(Notification.status == status)

        if channel is not None:
            filters.append(Notification.channel == channel)

        if is_read is not None:
            filters.append(Notification.is_read.is_(is_read))

        if entity_type is not None:
            filters.append(Notification.entity_type == entity_type)

        if entity_id is not None:
            filters.append(Notification.entity_id == entity_id)

        if created_from is not None:
            filters.append(Notification.created_at >= created_from)

        if created_to is not None:
            filters.append(Notification.created_at <= created_to)

        return filters
