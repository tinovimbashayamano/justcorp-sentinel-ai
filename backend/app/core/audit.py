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


class AuditStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
