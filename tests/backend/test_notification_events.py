"""Tests for notification-producing domain events."""

from backend.app.events.base import SynchronousEventBus
from backend.app.events.case_events import InvestigationAssigned
from backend.app.events.handlers.notification_handlers import (
    NotificationDomainEventHandlers,
)
from backend.app.events.registry import (
    register_notification_event_handlers,
)
from backend.app.services.notification_service import NotificationService


def test_investigation_assignment_creates_notification(
    db_session,
    test_user,
):
    service = NotificationService(db_session)
    handlers = NotificationDomainEventHandlers(service)
    event_bus = SynchronousEventBus()

    register_notification_event_handlers(event_bus, handlers)

    event = InvestigationAssigned(
        case_id=1001,
        assigned_user_id=test_user.id,
        assigned_by_user_id=test_user.id,
        case_reference="CASE-1001",
        correlation_id="test-correlation",
    )

    errors = event_bus.publish(
        event,
        raise_on_error=False,
    )

    notifications, total = service.list_notifications(
        recipient_user_id=test_user.id,
        entity_type="fraud_case",
        entity_id=1001,
        include_expired=True,
        limit=10,
    )

    assert errors == []
    assert total == 1
    assert notifications[0].title == "Investigation assigned"
    assert notifications[0].status == "delivered"
    assert (
        notifications[0].metadata_json["correlation_id"]
        == "test-correlation"
    )


def test_event_bus_does_not_duplicate_handler_registration(
    db_session,
    test_user,
):
    service = NotificationService(db_session)
    handlers = NotificationDomainEventHandlers(service)
    event_bus = SynchronousEventBus()

    register_notification_event_handlers(event_bus, handlers)
    register_notification_event_handlers(event_bus, handlers)

    assert event_bus.handler_count(InvestigationAssigned) == 1
