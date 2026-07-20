import logging
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from backend.app.core.audit import (
    AuditAction,
    AuditStatus,
)
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User


logger = logging.getLogger(__name__)


def get_client_ip(
    request: Request | None,
) -> str | None:
    if request is None:
        return None

    forwarded_for = request.headers.get(
        "x-forwarded-for"
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client is None:
        return None

    return request.client.host


def create_audit_log(
    db: Session,
    *,
    action: AuditAction | str,
    status: AuditStatus | str,
    user: User | None = None,
    actor_username: str | None = None,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    request: Request | None = None,
    details: dict[str, Any] | None = None,
    commit: bool = True,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user.id if user else None,
        actor_username=(
            user.username
            if user
            else actor_username
        ),
        action=str(action),
        status=str(status),
        resource_type=resource_type,
        resource_id=(
            str(resource_id)
            if resource_id is not None
            else None
        ),
        ip_address=get_client_ip(request),
        user_agent=(
            request.headers.get("user-agent")
            if request
            else None
        ),
        details=details,
    )

    db.add(audit_log)

    if commit:
        db.commit()
        db.refresh(audit_log)
    else:
        db.flush()

    return audit_log


def safely_create_audit_log(
    db: Session,
    **kwargs,
) -> AuditLog | None:
    try:
        return create_audit_log(
            db=db,
            **kwargs,
        )
    except Exception:
        db.rollback()

        logger.exception(
            "Failed to persist audit log."
        )

        return None


def list_audit_logs(
    db: Session,
    *,
    action: str | None = None,
    status: str | None = None,
    actor_username: str | None = None,
    resource_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    query = db.query(AuditLog)

    if action:
        query = query.filter(
            AuditLog.action == action
        )

    if status:
        query = query.filter(
            AuditLog.status == status
        )

    if actor_username:
        query = query.filter(
            AuditLog.actor_username
            == actor_username
        )

    if resource_type:
        query = query.filter(
            AuditLog.resource_type
            == resource_type
        )

    total = query.count()

    items = (
        query
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return items, total
