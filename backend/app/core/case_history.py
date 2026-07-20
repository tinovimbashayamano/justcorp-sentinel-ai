from enum import StrEnum


class CaseEvent(StrEnum):
    CREATED = "case.created"
    STATUS_CHANGED = "case.status_changed"
    PRIORITY_CHANGED = "case.priority_changed"
    ASSIGNED = "case.assigned"
    UNASSIGNED = "case.unassigned"
    REASSIGNED = "case.reassigned"
    COMMENT_ADDED = "case.comment_added"
    COMMENT_CREATED = "case.comment.created"
    COMMENT_UPDATED = "case.comment.updated"
    COMMENT_DELETED = "case.comment.deleted"
    CLOSED = "case.closed"
    REOPENED = "case.reopened"
