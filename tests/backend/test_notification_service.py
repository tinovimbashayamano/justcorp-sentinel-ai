"""Tests for notification lifecycle operations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.notification_service import (
    NotificationConflictError,
    NotificationService,
    NotificationValidationError,
)


def test_create_in_app_notification_is_delivered(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    notification = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="Test notification",
        message="Notification body",
    )

    assert notification.recipient_user_id == test_user.id
    assert notification.channel == "in_app"
    assert notification.status == "delivered"
    assert notification.delivered_at is not None
    assert notification.is_read is False


def test_create_notification_rejects_empty_title(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    with pytest.raises(NotificationValidationError):
        service.create_notification(
            recipient_user_id=test_user.id,
            notification_type="system",
            title=" ",
            message="Valid body",
        )


def test_create_notification_rejects_past_expiry(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    with pytest.raises(NotificationValidationError):
        service.create_notification(
            recipient_user_id=test_user.id,
            notification_type="system",
            title="Expired",
            message="Expired notification",
            expires_at=(
                datetime.now(timezone.utc) - timedelta(minutes=1)
            ),
        )


def test_duplicate_notification_refreshes_existing_record(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    first = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="Duplicate",
        message="First message",
        deduplication_key="duplicate-test",
    )

    second = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="Duplicate updated",
        message="Second message",
        deduplication_key="duplicate-test",
    )

    assert second.id == first.id
    assert second.message == "Second message"


def test_mark_notification_read_and_unread(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    notification = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="Read state",
        message="Testing read state",
    )

    read_notification = service.mark_as_read(
        notification_id=notification.id,
        recipient_user_id=test_user.id,
    )

    assert read_notification.is_read is True
    assert read_notification.read_at is not None

    unread_notification = service.mark_as_unread(
        notification_id=notification.id,
        recipient_user_id=test_user.id,
    )

    assert unread_notification.is_read is False
    assert unread_notification.read_at is None


def test_soft_delete_and_restore_notification(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    notification = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="Delete test",
        message="Delete and restore",
    )

    deleted = service.delete_notification(
        notification_id=notification.id,
        recipient_user_id=test_user.id,
        deleted_by_user_id=test_user.id,
    )

    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None

    restored = service.restore_notification(
        notification_id=notification.id,
        recipient_user_id=test_user.id,
    )

    assert restored.is_deleted is False
    assert restored.deleted_at is None
    assert restored.deleted_by_user_id is None


def test_failed_delivery_sets_retry_metadata(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    notification = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        channel="email",
        title="Retry test",
        message="Delivery should fail",
        auto_deliver_in_app=False,
    )

    failed = service.mark_failed(
        notification_id=notification.id,
        failure_reason="Provider unavailable",
    )

    assert failed.status == "failed"
    assert failed.delivery_attempts == 1
    assert failed.failure_reason == "Provider unavailable"
    assert failed.failed_at is not None
    assert failed.next_retry_at is not None


def test_delivered_notification_cannot_be_retried(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    notification = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="Delivered",
        message="Already delivered",
    )

    with pytest.raises(NotificationConflictError):
        service.retry_notification(notification_id=notification.id)


def test_unread_count_excludes_read_notifications(
    db_session,
    test_user,
):
    service = NotificationService(db_session)

    first = service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="First",
        message="First",
        deduplication_key="unread-first",
    )

    service.create_notification(
        recipient_user_id=test_user.id,
        notification_type="system",
        title="Second",
        message="Second",
        deduplication_key="unread-second",
    )

    service.mark_as_read(
        notification_id=first.id,
        recipient_user_id=test_user.id,
    )

    assert service.get_unread_count(
        recipient_user_id=test_user.id
    ) >= 1
