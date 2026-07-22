from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.dependencies import (
    AdminAnalystOrAuditor,
    AdminOrAnalyst,
    AdminUser,
    CurrentUser,
)
from backend.app.core.investigation_tasks import (
    InvestigationTaskEvent,
    InvestigationTaskStatus,
)
from backend.app.db.session import get_db
from backend.app.models.investigation_task import InvestigationTask
from backend.app.models.user import User
from backend.app.schemas.investigation_task import (
    InvestigationTaskAssignment,
    InvestigationTaskCancellation,
    InvestigationTaskCompletion,
    InvestigationTaskCreate,
    InvestigationTaskDeleteResponse,
    InvestigationTaskListResponse,
    InvestigationTaskResponse,
    InvestigationTaskStatusUpdate,
    InvestigationTaskUpdate,
)
from backend.app.services.audit_service import create_audit_log
from backend.app.services.case_history_service import create_case_history
from backend.app.services.investigation_task_service import (
    assign_task,
    calculate_is_overdue,
    cancel_task,
    change_task_status,
    complete_task,
    create_task,
    get_active_case_or_404,
    get_task_or_404,
    list_tasks,
    require_task_worker_or_privileged,
    soft_delete_task,
    update_task,
)


router = APIRouter(
    prefix="/fraud-cases/{case_id}/tasks",
    tags=["Investigation Tasks"],
)

TASK_RESOURCE_TYPE = "investigation_task"

ASSIGNMENT_AUDIT_ACTIONS = {
    InvestigationTaskEvent.ASSIGNED.value: AuditAction.INVESTIGATION_TASK_ASSIGNED,
    InvestigationTaskEvent.REASSIGNED.value: (
        AuditAction.INVESTIGATION_TASK_REASSIGNED
    ),
    InvestigationTaskEvent.UNASSIGNED.value: (
        AuditAction.INVESTIGATION_TASK_UNASSIGNED
    ),
}


def to_response(task: InvestigationTask) -> InvestigationTaskResponse:
    response = InvestigationTaskResponse.model_validate(task)
    return response.model_copy(
        update={"is_overdue": calculate_is_overdue(task)}
    )


def _task_metadata(task: InvestigationTask) -> dict[str, Any]:
    return {
        "case_id": task.case_id,
        "task_id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "assigned_to_user_id": task.assigned_to_user_id,
        "assigned_to_username": task.assigned_to_username,
    }


def _record_task_action(
    db: Session,
    *,
    task: InvestigationTask,
    actor: User,
    request: Request,
    audit_action: AuditAction,
    history_event: InvestigationTaskEvent | str,
    additional_details: dict[str, Any] | None = None,
) -> None:
    details = _task_metadata(task)

    if additional_details:
        details.update(additional_details)

    create_audit_log(
        db=db,
        action=audit_action,
        status=AuditStatus.SUCCESS,
        user=actor,
        resource_type=TASK_RESOURCE_TYPE,
        resource_id=task.id,
        request=request,
        details=details,
        commit=False,
    )
    create_case_history(
        db=db,
        case=get_active_case_or_404(db, task.case_id),
        user=actor,
        event_type=history_event,
        details={
            key: value
            for key, value in details.items()
            if key != "case_id"
        },
        commit=False,
    )


def _commit_task(db: Session, task: InvestigationTask) -> None:
    db.commit()
    db.refresh(task)


@router.post(
    "",
    response_model=InvestigationTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_investigation_task(
    case_id: int,
    payload: InvestigationTaskCreate,
    request: Request,
    current_user: AdminOrAnalyst,
    db: Session = Depends(get_db),
) -> InvestigationTaskResponse:
    try:
        task = create_task(
            db,
            case_id=case_id,
            payload=payload,
            actor=current_user,
        )
        _record_task_action(
            db,
            task=task,
            actor=current_user,
            request=request,
            audit_action=AuditAction.INVESTIGATION_TASK_CREATED,
            history_event=InvestigationTaskEvent.CREATED,
        )
        _commit_task(db, task)
        return to_response(task)
    except Exception:
        db.rollback()
        raise


@router.get("", response_model=InvestigationTaskListResponse)
def list_investigation_tasks(
    case_id: int,
    _: AdminAnalystOrAuditor,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    task_status: InvestigationTaskStatus | None = Query(
        default=None,
        alias="status",
    ),
    assigned_to_user_id: int | None = Query(default=None, ge=1),
    overdue_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> InvestigationTaskListResponse:
    tasks, total = list_tasks(
        db,
        case_id=case_id,
        limit=limit,
        offset=offset,
        task_status=task_status,
        assigned_to_user_id=assigned_to_user_id,
        overdue_only=overdue_only,
    )
    return InvestigationTaskListResponse(
        items=[to_response(task) for task in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=InvestigationTaskResponse)
def read_investigation_task(
    case_id: int,
    task_id: int,
    _: AdminAnalystOrAuditor,
    db: Session = Depends(get_db),
) -> InvestigationTaskResponse:
    return to_response(get_task_or_404(db, case_id, task_id))


@router.patch("/{task_id}", response_model=InvestigationTaskResponse)
def update_investigation_task(
    case_id: int,
    task_id: int,
    payload: InvestigationTaskUpdate,
    request: Request,
    current_user: AdminOrAnalyst,
    db: Session = Depends(get_db),
) -> InvestigationTaskResponse:
    try:
        task = update_task(
            db,
            case_id=case_id,
            task_id=task_id,
            payload=payload,
        )
        _record_task_action(
            db,
            task=task,
            actor=current_user,
            request=request,
            audit_action=AuditAction.INVESTIGATION_TASK_UPDATED,
            history_event=InvestigationTaskEvent.UPDATED,
        )
        _commit_task(db, task)
        return to_response(task)
    except Exception:
        db.rollback()
        raise


@router.patch(
    "/{task_id}/assignment",
    response_model=InvestigationTaskResponse,
)
def assign_investigation_task(
    case_id: int,
    task_id: int,
    payload: InvestigationTaskAssignment,
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> InvestigationTaskResponse:
    try:
        existing_task = get_task_or_404(db, case_id, task_id)
        previous_user_id = existing_task.assigned_to_user_id
        previous_username = existing_task.assigned_to_username
        task, event_name = assign_task(
            db,
            case_id=case_id,
            task_id=task_id,
            payload=payload,
        )
        _record_task_action(
            db,
            task=task,
            actor=current_user,
            request=request,
            audit_action=ASSIGNMENT_AUDIT_ACTIONS[event_name],
            history_event=event_name,
            additional_details={
                "previous_assigned_to_user_id": previous_user_id,
                "previous_assigned_to_username": previous_username,
            },
        )
        _commit_task(db, task)
        return to_response(task)
    except Exception:
        db.rollback()
        raise


@router.patch("/{task_id}/status", response_model=InvestigationTaskResponse)
def update_investigation_task_status(
    case_id: int,
    task_id: int,
    payload: InvestigationTaskStatusUpdate,
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> InvestigationTaskResponse:
    try:
        existing_task = get_task_or_404(db, case_id, task_id)
        require_task_worker_or_privileged(
            task=existing_task,
            current_user=current_user,
        )
        task, previous_status = change_task_status(
            db,
            case_id=case_id,
            task_id=task_id,
            payload=payload,
        )
        _record_task_action(
            db,
            task=task,
            actor=current_user,
            request=request,
            audit_action=AuditAction.INVESTIGATION_TASK_STATUS_CHANGED,
            history_event=InvestigationTaskEvent.STATUS_CHANGED,
            additional_details={"previous_status": previous_status},
        )
        _commit_task(db, task)
        return to_response(task)
    except Exception:
        db.rollback()
        raise


@router.post("/{task_id}/complete", response_model=InvestigationTaskResponse)
def complete_investigation_task(
    case_id: int,
    task_id: int,
    payload: InvestigationTaskCompletion,
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> InvestigationTaskResponse:
    try:
        existing_task = get_task_or_404(db, case_id, task_id)
        require_task_worker_or_privileged(
            task=existing_task,
            current_user=current_user,
        )
        task = complete_task(
            db,
            case_id=case_id,
            task_id=task_id,
            payload=payload,
            actor=current_user,
        )
        _record_task_action(
            db,
            task=task,
            actor=current_user,
            request=request,
            audit_action=AuditAction.INVESTIGATION_TASK_COMPLETED,
            history_event=InvestigationTaskEvent.COMPLETED,
        )
        _commit_task(db, task)
        return to_response(task)
    except Exception:
        db.rollback()
        raise


@router.post("/{task_id}/cancel", response_model=InvestigationTaskResponse)
def cancel_investigation_task(
    case_id: int,
    task_id: int,
    payload: InvestigationTaskCancellation,
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> InvestigationTaskResponse:
    try:
        task = cancel_task(
            db,
            case_id=case_id,
            task_id=task_id,
            payload=payload,
            actor=current_user,
        )
        _record_task_action(
            db,
            task=task,
            actor=current_user,
            request=request,
            audit_action=AuditAction.INVESTIGATION_TASK_CANCELLED,
            history_event=InvestigationTaskEvent.CANCELLED,
        )
        _commit_task(db, task)
        return to_response(task)
    except Exception:
        db.rollback()
        raise


@router.delete(
    "/{task_id}",
    response_model=InvestigationTaskDeleteResponse,
)
def delete_investigation_task(
    case_id: int,
    task_id: int,
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> InvestigationTaskDeleteResponse:
    try:
        task = soft_delete_task(
            db,
            case_id=case_id,
            task_id=task_id,
            actor=current_user,
        )
        _record_task_action(
            db,
            task=task,
            actor=current_user,
            request=request,
            audit_action=AuditAction.INVESTIGATION_TASK_DELETED,
            history_event=InvestigationTaskEvent.DELETED,
        )
        _commit_task(db, task)
        return InvestigationTaskDeleteResponse(
            id=task.id,
            task_id=task.id,
            case_id=task.case_id,
            title=task.title,
            is_deleted=task.is_deleted,
            deleted_by_username=task.deleted_by_username,
            deleted_at=task.deleted_at,
        )
    except Exception:
        db.rollback()
        raise
