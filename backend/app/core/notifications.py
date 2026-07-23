"""Constants and helpers for the notification and alert engine."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class NotificationType(StrEnum):
    """Supported notification event categories."""

    FRAUD_ALERT = "fraud_alert"
    CASE_ASSIGNED = "case_assigned"
    CASE_STATUS_CHANGED = "case_status_changed"
    CASE_ESCALATED = "case_escalated"
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_DUE_SOON = "task_due_soon"
    TASK_OVERDUE = "task_overdue"
    REPORT_COMPLETED = "report_completed"
    REPORT_FAILED = "report_failed"
    EVIDENCE_ADDED = "evidence_added"
    COMMENT_ADDED = "comment_added"
    USER_MENTIONED = "user_mentioned"
    SYSTEM = "system"


class NotificationPriority(StrEnum):
    """Operational importance assigned to a notification."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(StrEnum):
    """Delivery channels supported by the notification engine."""

    IN_APP = "in_app"
    EMAIL = "email"


class NotificationStatus(StrEnum):
    """Current notification delivery state."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationEntityType(StrEnum):
    """Domain resource associated with a notification."""

    FRAUD_SCORE = "fraud_score"
    FRAUD_CASE = "fraud_case"
    INVESTIGATION_TASK = "investigation_task"
    GENERATED_REPORT = "generated_report"
    CASE_EVIDENCE = "case_evidence"
    CASE_COMMENT = "case_comment"
    SYSTEM = "system"


NOTIFICATION_READ_ROLES: Final[frozenset[str]] = frozenset(
    {
        "admin",
        "fraud_analyst",
        "risk_manager",
        "manager",
        "auditor",
    }
)

NOTIFICATION_ADMIN_ROLES: Final[frozenset[str]] = frozenset({"admin"})

NOTIFICATION_SYSTEM_ROLES: Final[frozenset[str]] = frozenset(
    {
        "admin",
        "system",
    }
)

DEFAULT_NOTIFICATION_CHANNEL: Final[str] = NotificationChannel.IN_APP.value
DEFAULT_NOTIFICATION_PRIORITY: Final[str] = NotificationPriority.NORMAL.value
DEFAULT_NOTIFICATION_STATUS: Final[str] = NotificationStatus.PENDING.value

DEFAULT_MAX_DELIVERY_ATTEMPTS: Final[int] = 3
DEFAULT_NOTIFICATION_PAGE_SIZE: Final[int] = 25
MAX_NOTIFICATION_PAGE_SIZE: Final[int] = 100

HIGH_PRIORITY_TYPES: Final[frozenset[str]] = frozenset(
    {
        NotificationType.FRAUD_ALERT.value,
        NotificationType.CASE_ESCALATED.value,
        NotificationType.TASK_OVERDUE.value,
        NotificationType.REPORT_FAILED.value,
    }
)

CRITICAL_NOTIFICATION_TYPES: Final[frozenset[str]] = frozenset(
    {
        NotificationType.FRAUD_ALERT.value,
        NotificationType.CASE_ESCALATED.value,
    }
)


def default_priority_for_type(notification_type: str) -> str:
    """Return an appropriate default priority for a notification type."""

    normalized = str(notification_type).strip().lower()
    if normalized in CRITICAL_NOTIFICATION_TYPES:
        return NotificationPriority.CRITICAL.value
    if normalized in HIGH_PRIORITY_TYPES:
        return NotificationPriority.HIGH.value
    return DEFAULT_NOTIFICATION_PRIORITY
