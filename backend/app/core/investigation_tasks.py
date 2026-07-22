from enum import StrEnum


class InvestigationTaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvestigationTaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InvestigationTaskEvent(StrEnum):
    CREATED = "case.task.created"
    UPDATED = "case.task.updated"
    ASSIGNED = "case.task.assigned"
    REASSIGNED = "case.task.reassigned"
    UNASSIGNED = "case.task.unassigned"
    STATUS_CHANGED = "case.task.status_changed"
    COMPLETED = "case.task.completed"
    CANCELLED = "case.task.cancelled"
    DELETED = "case.task.deleted"


TERMINAL_TASK_STATUSES: frozenset[InvestigationTaskStatus] = frozenset(
    {
        InvestigationTaskStatus.COMPLETED,
        InvestigationTaskStatus.CANCELLED,
    }
)


VALID_TASK_STATUS_TRANSITIONS: dict[
    InvestigationTaskStatus,
    frozenset[InvestigationTaskStatus],
] = {
    InvestigationTaskStatus.PENDING: frozenset(
        {
            InvestigationTaskStatus.IN_PROGRESS,
            InvestigationTaskStatus.BLOCKED,
            InvestigationTaskStatus.CANCELLED,
        }
    ),
    InvestigationTaskStatus.IN_PROGRESS: frozenset(
        {
            InvestigationTaskStatus.BLOCKED,
            InvestigationTaskStatus.COMPLETED,
            InvestigationTaskStatus.CANCELLED,
        }
    ),
    InvestigationTaskStatus.BLOCKED: frozenset(
        {
            InvestigationTaskStatus.PENDING,
            InvestigationTaskStatus.IN_PROGRESS,
            InvestigationTaskStatus.CANCELLED,
        }
    ),
    InvestigationTaskStatus.COMPLETED: frozenset(),
    InvestigationTaskStatus.CANCELLED: frozenset(),
}


def is_valid_task_status_transition(
    current_status: InvestigationTaskStatus,
    new_status: InvestigationTaskStatus,
) -> bool:
    """Return whether a task status transition is permitted."""

    if current_status == new_status:
        return False

    allowed_statuses = VALID_TASK_STATUS_TRANSITIONS.get(
        current_status,
        frozenset(),
    )

    return new_status in allowed_statuses
