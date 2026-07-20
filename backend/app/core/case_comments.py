from enum import StrEnum


class CommentVisibility(StrEnum):
    INTERNAL = "internal"
    AUDITOR_VISIBLE = "auditor_visible"


class CommentEvent(StrEnum):
    CREATED = "case.comment.created"
    UPDATED = "case.comment.updated"
    DELETED = "case.comment.deleted"
