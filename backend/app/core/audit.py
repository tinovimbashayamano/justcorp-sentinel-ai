from enum import StrEnum


class AuditAction(StrEnum):
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    LOGOUT_ALL = "auth.logout_all"
    PASSWORD_CHANGE = "auth.password_change"

    USER_ROLE_UPDATE = "admin.user.role_update"
    USER_STATUS_UPDATE = "admin.user.status_update"
    ADMIN_ACCESS_DENIED = "admin.access_denied"

    FRAUD_SCORE = "fraud.score"
    FRAUD_SCORE_SAVE = "fraud.score_save"

    CASE_CREATE = "case.create"
    CASE_UPDATE = "case.update"
    CASE_ASSIGNED = "case.assignment.assigned"
    CASE_REASSIGNED = "case.assignment.reassigned"
    CASE_UNASSIGNED = "case.assignment.unassigned"

    CASE_COMMENT_CREATE = "case.comment.create"
    CASE_COMMENT_UPDATE = "case.comment.update"
    CASE_COMMENT_DELETE = "case.comment.delete"
    CASE_COMMENT_ACCESS_DENIED = "case.comment.access_denied"

    CASE_EVIDENCE_UPLOAD = "case.evidence.upload"
    CASE_EVIDENCE_DOWNLOAD = "case.evidence.download"
    CASE_EVIDENCE_DELETE = "case.evidence.delete"
    CASE_EVIDENCE_ACCESS_DENIED = "case.evidence.access_denied"

    INVESTIGATION_TASK_CREATED = "investigation_task.created"
    INVESTIGATION_TASK_UPDATED = "investigation_task.updated"
    INVESTIGATION_TASK_ASSIGNED = "investigation_task.assigned"
    INVESTIGATION_TASK_REASSIGNED = "investigation_task.reassigned"
    INVESTIGATION_TASK_UNASSIGNED = "investigation_task.unassigned"
    INVESTIGATION_TASK_STATUS_CHANGED = "investigation_task.status_changed"
    INVESTIGATION_TASK_COMPLETED = "investigation_task.completed"
    INVESTIGATION_TASK_CANCELLED = "investigation_task.cancelled"
    INVESTIGATION_TASK_DELETED = "investigation_task.deleted"
    INVESTIGATION_TASK_VIEWED = "investigation_task.viewed"


class AuditStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
