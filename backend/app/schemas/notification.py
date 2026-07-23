"""Pydantic schemas for the notification API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Public representation of a notification."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_user_id: int
    actor_user_id: int | None = None

    notification_type: str
    priority: str
    channel: str
    status: str

    title: str
    message: str

    entity_type: str | None = None
    entity_id: int | None = None
    action_url: str | None = None

    metadata_json: dict[str, Any] | None = None
    deduplication_key: str | None = None

    is_read: bool
    read_at: datetime | None = None

    delivery_attempts: int
    max_delivery_attempts: int
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    failure_reason: str | None = None
    next_retry_at: datetime | None = None

    expires_at: datetime | None = None

    is_deleted: bool
    deleted_at: datetime | None = None
    deleted_by_user_id: int | None = None

    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated notification response."""

    items: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class NotificationUnreadCountResponse(BaseModel):
    """Unread-notification count."""

    unread_count: int


class NotificationStatisticsResponse(BaseModel):
    """Notification summary statistics."""

    total: int
    unread: int
    critical: int
    pending: int
    failed: int
    today: int


class NotificationIdsRequest(BaseModel):
    """Request containing one or more notification IDs."""

    notification_ids: list[int] = Field(
        min_length=1,
        max_length=100,
    )


class NotificationBulkOperationResponse(BaseModel):
    """Result of a bulk notification operation."""

    affected_count: int


class NotificationAdminCreateRequest(BaseModel):
    """Administrative notification creation request."""

    recipient_user_id: int = Field(gt=0)
    actor_user_id: int | None = Field(default=None, gt=0)

    notification_type: str = Field(
        default="system",
        min_length=1,
        max_length=50,
    )
    priority: str = Field(
        default="normal",
        min_length=1,
        max_length=20,
    )
    channel: str = Field(
        default="in_app",
        min_length=1,
        max_length=20,
    )

    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)

    entity_type: str | None = Field(default=None, max_length=100)
    entity_id: int | None = Field(default=None, gt=0)
    action_url: str | None = Field(default=None, max_length=1000)

    metadata: dict[str, Any] | None = None
    deduplication_key: str | None = Field(
        default=None,
        max_length=255,
    )

    expires_at: datetime | None = None
    max_delivery_attempts: int = Field(default=3, ge=1, le=20)


class NotificationEmailRequest(BaseModel):
    """Request for creating and delivering an email notification."""

    recipient_user_id: int = Field(gt=0)
    actor_user_id: int | None = Field(default=None, gt=0)

    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    priority: str = Field(default="normal", max_length=20)

    entity_type: str | None = Field(default=None, max_length=100)
    entity_id: int | None = Field(default=None, gt=0)
    action_url: str | None = Field(default=None, max_length=1000)

    metadata: dict[str, Any] | None = None
    deduplication_key: str | None = Field(
        default=None,
        max_length=255,
    )


class NotificationRetryQueueResponse(BaseModel):
    """Email retry-queue processing result."""

    examined: int
    delivered: int
    failed: int
    skipped: int
