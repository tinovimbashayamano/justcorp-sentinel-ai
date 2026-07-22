from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.investigation_tasks import (
    InvestigationTaskEvent,
    InvestigationTaskStatus,
    TERMINAL_TASK_STATUSES,
    is_valid_task_status_transition,
)
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.investigation_task import InvestigationTask
from backend.app.models.user import User
from backend.app.schemas.investigation_task import (
    InvestigationTaskAssignment,
    InvestigationTaskCancellation,
    InvestigationTaskCompletion,
    InvestigationTaskCreate,
    InvestigationTaskStatusUpdate,
    InvestigationTaskUpdate,
)


ASSIGNABLE_ROLES = {
    "admin",
    "fraud_analyst",
    "analyst",
    "risk_analyst",
}

PRIVILEGED_TASK_ROLES = {
    "admin",
    "risk_manager",
    "manager",
}

TASK_WORKER_ROLES = {
    "fraud_analyst",
    "analyst",
    "risk_analyst",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_active_case_or_404(
    db: Session,
    case_id: int,
) -> FraudCaseReview:
    fraud_case = db.scalar(
        select(FraudCaseReview).where(
            FraudCaseReview.id == case_id,
        )
    )

    if fraud_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fraud case not found.",
        )

    return fraud_case


def get_task_or_404(
    db: Session,
    case_id: int,
    task_id: int,
    *,
    include_deleted: bool = False,
) -> InvestigationTask:
    statement = select(InvestigationTask).where(
        InvestigationTask.id == task_id,
        InvestigationTask.case_id == case_id,
    )

    if not include_deleted:
        statement = statement.where(
            InvestigationTask.is_deleted.is_(False)
        )

    task = db.scalar(statement)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation task not found.",
        )

    return task


def get_assignable_user_or_404(
    db: Session,
    user_id: int,
) -> User:
    user = db.scalar(
        select(User).where(
            User.id == user_id,
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasks cannot be assigned to an inactive user.",
        )

    role_value = getattr(user.role, "value", user.role)

    if str(role_value).lower() not in ASSIGNABLE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected user cannot be assigned investigation tasks.",
        )

    return user


def assert_task_is_mutable(task: InvestigationTask) -> None:
    current_status = InvestigationTaskStatus(task.status)

    if current_status in TERMINAL_TASK_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Completed or cancelled tasks cannot be modified.",
        )


def require_task_worker_or_privileged(
    *,
    task: InvestigationTask,
    current_user: User,
) -> None:
    role = getattr(current_user.role, "value", current_user.role)
    normalized_role = str(role).lower()

    if normalized_role in PRIVILEGED_TASK_ROLES:
        return

    if (
        normalized_role in TASK_WORKER_ROLES
        and task.assigned_to_user_id == current_user.id
    ):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to perform this task action.",
    )


def calculate_is_overdue(task: InvestigationTask) -> bool:
    if task.is_deleted or task.due_at is None:
        return False

    current_status = InvestigationTaskStatus(task.status)

    if current_status in TERMINAL_TASK_STATUSES:
        return False

    due_at = task.due_at

    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)

    return due_at < utc_now()


def create_task(
    db: Session,
    *,
    case_id: int,
    payload: InvestigationTaskCreate,
    actor: User,
) -> InvestigationTask:
    get_active_case_or_404(db, case_id)

    assigned_user = None

    if payload.assigned_to_user_id is not None:
        assigned_user = get_assignable_user_or_404(
            db,
            payload.assigned_to_user_id,
        )

    task = InvestigationTask(
        case_id=case_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        status=InvestigationTaskStatus.PENDING.value,
        due_at=payload.due_at,
        created_by_user_id=actor.id,
        created_by_username=actor.username,
        assigned_to_user_id=(assigned_user.id if assigned_user else None),
        assigned_to_username=(
            assigned_user.username if assigned_user else None
        ),
    )

    db.add(task)
    db.flush()

    return task


def list_tasks(
    db: Session,
    *,
    case_id: int,
    limit: int,
    offset: int,
    task_status: InvestigationTaskStatus | None = None,
    assigned_to_user_id: int | None = None,
    overdue_only: bool = False,
) -> tuple[list[InvestigationTask], int]:
    get_active_case_or_404(db, case_id)

    filters = [
        InvestigationTask.case_id == case_id,
        InvestigationTask.is_deleted.is_(False),
    ]

    if task_status is not None:
        filters.append(InvestigationTask.status == task_status.value)

    if assigned_to_user_id is not None:
        filters.append(
            InvestigationTask.assigned_to_user_id == assigned_to_user_id
        )

    if overdue_only:
        filters.extend(
            [
                InvestigationTask.due_at.is_not(None),
                InvestigationTask.due_at < utc_now(),
                InvestigationTask.status.notin_(
                    [
                        InvestigationTaskStatus.COMPLETED.value,
                        InvestigationTaskStatus.CANCELLED.value,
                    ]
                ),
            ]
        )

    total = db.scalar(
        select(func.count(InvestigationTask.id)).where(*filters)
    ) or 0

    tasks = list(
        db.scalars(
            select(InvestigationTask)
            .where(*filters)
            .order_by(
                InvestigationTask.created_at.desc(),
                InvestigationTask.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
    )

    return tasks, total


def update_task(
    db: Session,
    *,
    case_id: int,
    task_id: int,
    payload: InvestigationTaskUpdate,
) -> InvestigationTask:
    task = get_task_or_404(db, case_id, task_id)
    assert_task_is_mutable(task)

    if payload.title is not None:
        task.title = payload.title

    if payload.clear_description:
        task.description = None
    elif payload.description is not None:
        task.description = payload.description

    if payload.priority is not None:
        task.priority = payload.priority.value

    if payload.clear_due_at:
        task.due_at = None
    elif payload.due_at is not None:
        task.due_at = payload.due_at

    task.updated_at = utc_now()
    db.flush()

    return task


def assign_task(
    db: Session,
    *,
    case_id: int,
    task_id: int,
    payload: InvestigationTaskAssignment,
) -> tuple[InvestigationTask, str]:
    task = get_task_or_404(db, case_id, task_id)
    assert_task_is_mutable(task)

    previous_user_id = task.assigned_to_user_id

    if payload.assigned_to_user_id is None:
        if previous_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task is already unassigned.",
            )

        task.assigned_to_user_id = None
        task.assigned_to_username = None
        event = InvestigationTaskEvent.UNASSIGNED.value
    else:
        assigned_user = get_assignable_user_or_404(
            db,
            payload.assigned_to_user_id,
        )

        if previous_user_id == assigned_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task is already assigned to this user.",
            )

        task.assigned_to_user_id = assigned_user.id
        task.assigned_to_username = assigned_user.username
        event = (
            InvestigationTaskEvent.ASSIGNED.value
            if previous_user_id is None
            else InvestigationTaskEvent.REASSIGNED.value
        )

    task.updated_at = utc_now()
    db.flush()

    return task, event


def change_task_status(
    db: Session,
    *,
    case_id: int,
    task_id: int,
    payload: InvestigationTaskStatusUpdate,
) -> tuple[InvestigationTask, str]:
    task = get_task_or_404(db, case_id, task_id)

    current_status = InvestigationTaskStatus(task.status)
    new_status = payload.status

    if not is_valid_task_status_transition(current_status, new_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid task transition: "
                f"{current_status.value} -> {new_status.value}."
            ),
        )

    task.status = new_status.value
    task.updated_at = utc_now()
    db.flush()

    return task, current_status.value


def complete_task(
    db: Session,
    *,
    case_id: int,
    task_id: int,
    payload: InvestigationTaskCompletion,
    actor: User,
) -> InvestigationTask:
    task = get_task_or_404(db, case_id, task_id)
    current_status = InvestigationTaskStatus(task.status)

    if not is_valid_task_status_transition(
        current_status,
        InvestigationTaskStatus.COMPLETED,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task cannot be completed from {current_status.value}.",
        )

    now = utc_now()
    task.status = InvestigationTaskStatus.COMPLETED.value
    task.completed_by_user_id = actor.id
    task.completed_by_username = actor.username
    task.completed_at = now
    task.completion_note = payload.completion_note
    task.updated_at = now

    db.flush()
    return task


def cancel_task(
    db: Session,
    *,
    case_id: int,
    task_id: int,
    payload: InvestigationTaskCancellation,
    actor: User,
) -> InvestigationTask:
    task = get_task_or_404(db, case_id, task_id)
    current_status = InvestigationTaskStatus(task.status)

    if not is_valid_task_status_transition(
        current_status,
        InvestigationTaskStatus.CANCELLED,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task cannot be cancelled from {current_status.value}.",
        )

    now = utc_now()
    task.status = InvestigationTaskStatus.CANCELLED.value
    task.cancelled_by_user_id = actor.id
    task.cancelled_by_username = actor.username
    task.cancelled_at = now
    task.cancellation_reason = payload.cancellation_reason
    task.updated_at = now

    db.flush()
    return task


def soft_delete_task(
    db: Session,
    *,
    case_id: int,
    task_id: int,
    actor: User,
) -> InvestigationTask:
    task = get_task_or_404(db, case_id, task_id)
    now = utc_now()

    task.is_deleted = True
    task.deleted_by_user_id = actor.id
    task.deleted_by_username = actor.username
    task.deleted_at = now
    task.updated_at = now

    db.flush()
    return task
