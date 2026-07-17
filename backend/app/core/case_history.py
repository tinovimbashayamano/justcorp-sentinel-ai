from enum import StrEnum


class CaseEvent(StrEnum):
    CREATED = "case.created"
    STATUS_CHANGED = "case.status_changed"
    PRIORITY_CHANGED = "case.priority_changed"
    ASSIGNED = "case.assigned"
    COMMENT_ADDED = "case.comment_added"
    CLOSED = "case.closed"
    REOPENED = "case.reopened"
