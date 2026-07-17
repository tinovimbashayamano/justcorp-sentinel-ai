from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_roles
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.audit import AuditLogListResponse
from backend.app.services.audit_service import list_audit_logs


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


AuditReader = Annotated[
    User,
    Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.AUDITOR,
        )
    ),
]


@router.get(
    "",
    response_model=AuditLogListResponse,
)
def get_audit_logs(
    current_user: AuditReader,
    db: Session = Depends(get_db),
    action: str | None = Query(default=None),
    status: str | None = Query(default=None),
    actor_username: str | None = Query(
        default=None
    ),
    resource_type: str | None = Query(
        default=None
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    items, total = list_audit_logs(
        db=db,
        action=action,
        status=status,
        actor_username=actor_username,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
