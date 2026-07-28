from sqlalchemy import case as sql_case, desc, func
from sqlalchemy.orm import Session, selectinload

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.case_history import CaseEvent
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User, UserRole
from backend.app.schemas.fraud_case import (
    FraudCaseCreateRequest,
    FraudCaseUpdateRequest,
)
from backend.app.services.audit_service import create_audit_log
from backend.app.services.case_history_service import create_case_history


VALID_CASE_STATUSES = {
    "new",
    "open",
    "assigned",
    "investigating",
    "pending_customer",
    "escalated",
    "resolved",
    "under_review",
    "confirmed_fraud",
    "false_positive",
    "closed",
}

VALID_ANALYST_DECISIONS = {
    "pending",
    "confirmed_fraud",
    "false_positive",
    "needs_more_information",
}

VALID_CASE_PRIORITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


class FraudCaseNotFoundError(ValueError):
    pass


class CaseAssigneeNotFoundError(ValueError):
    pass


class InvalidCaseAssigneeError(ValueError):
    pass


def validate_case_status(case_status: str) -> None:
    if case_status not in VALID_CASE_STATUSES:
        raise ValueError(
            f"Invalid case_status '{case_status}'. "
            f"Allowed values: {sorted(VALID_CASE_STATUSES)}"
        )


def validate_analyst_decision(analyst_decision: str | None) -> None:
    if analyst_decision is None:
        return

    if analyst_decision not in VALID_ANALYST_DECISIONS:
        raise ValueError(
            f"Invalid analyst_decision '{analyst_decision}'. "
            f"Allowed values: {sorted(VALID_ANALYST_DECISIONS)}"
        )


def validate_case_priority(priority: str) -> None:
    if priority not in VALID_CASE_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. "
            f"Allowed values: {sorted(VALID_CASE_PRIORITIES)}"
        )


def create_fraud_case(
    db: Session,
    request: FraudCaseCreateRequest,
    user: User | None = None,
) -> FraudCaseReview:
    score_record = db.get(FraudScoreRecord, request.fraud_score_record_id)

    if score_record is None:
        raise ValueError(
            f"Fraud score record {request.fraud_score_record_id} does not exist."
        )

    validate_case_status(request.case_status)
    validate_case_priority(request.priority)
    validate_analyst_decision(request.analyst_decision)

    case = FraudCaseReview(
        fraud_score_record_id=request.fraud_score_record_id,
        case_status=request.case_status,
        priority=request.priority,
        assigned_to=request.assigned_to,
        closure_reason=request.closure_reason,
        analyst_decision=request.analyst_decision,
        analyst_notes=request.analyst_notes,
        reviewed_by=request.reviewed_by,
    )

    db.add(case)
    db.flush()

    create_case_history(
        db=db,
        case=case,
        user=user,
        event_type=CaseEvent.CREATED,
        details={
            "status": case.case_status,
            "priority": case.priority,
        },
    )

    db.refresh(case)

    return case


def list_fraud_cases(
    db: Session,
    limit: int = 20,
    case_status: str | None = None,
    assigned_to_user_id: int | None = None,
    unassigned: bool = False,
) -> list[FraudCaseReview]:
    if assigned_to_user_id is not None and unassigned:
        raise ValueError(
            "assigned_to_user_id and unassigned cannot both be supplied."
        )

    query = db.query(FraudCaseReview).options(
        selectinload(FraudCaseReview.assigned_to_user)
    )

    if case_status is not None:
        validate_case_status(case_status)
        query = query.filter(FraudCaseReview.case_status == case_status)

    if assigned_to_user_id is not None:
        query = query.filter(
            FraudCaseReview.assigned_to_user_id == assigned_to_user_id
        )
    elif unassigned:
        query = query.filter(FraudCaseReview.assigned_to_user_id.is_(None))

    return query.order_by(desc(FraudCaseReview.created_at)).limit(limit).all()


def get_fraud_case(
    db: Session,
    case_id: int,
) -> FraudCaseReview | None:
    return db.get(FraudCaseReview, case_id)


def update_fraud_case(
    db: Session,
    case_id: int,
    request: FraudCaseUpdateRequest,
    user: User | None = None,
) -> FraudCaseReview:
    case = db.get(FraudCaseReview, case_id)

    if case is None:
        raise ValueError(f"Fraud case {case_id} does not exist.")

    update_data = request.model_dump(exclude_unset=True)

    if "case_status" in update_data and update_data["case_status"] is not None:
        validate_case_status(update_data["case_status"])

    if "priority" in update_data and update_data["priority"] is not None:
        validate_case_priority(update_data["priority"])

    if (
        "analyst_decision" in update_data
        and update_data["analyst_decision"] is not None
    ):
        validate_analyst_decision(update_data["analyst_decision"])

    changes = {
        field: {
            "old": getattr(case, field),
            "new": value,
        }
        for field, value in update_data.items()
        if getattr(case, field) != value
    }

    for field, value in update_data.items():
        setattr(case, field, value)

    db.flush()

    history_events: list[
        tuple[CaseEvent, dict]
    ] = []

    if "case_status" in changes:
        old_status = changes["case_status"]["old"]
        new_status = changes["case_status"]["new"]

        if new_status == "closed":
            history_events.append(
                (
                    CaseEvent.CLOSED,
                    {
                        "old": old_status,
                        "new": new_status,
                        "reason": case.closure_reason,
                    },
                )
            )
        elif old_status == "closed":
            history_events.append(
                (
                    CaseEvent.REOPENED,
                    {
                        "old": old_status,
                        "new": new_status,
                    },
                )
            )
        else:
            history_events.append(
                (
                    CaseEvent.STATUS_CHANGED,
                    {
                        "old": old_status,
                        "new": new_status,
                    },
                )
            )

    if "priority" in changes:
        history_events.append(
            (
                CaseEvent.PRIORITY_CHANGED,
                changes["priority"],
            )
        )

    if "assigned_to" in changes:
        history_events.append(
            (
                CaseEvent.ASSIGNED,
                {
                    "old": changes["assigned_to"]["old"],
                    "assigned_to": changes["assigned_to"]["new"],
                },
            )
        )

    if "analyst_notes" in changes:
        history_events.append(
            (
                CaseEvent.COMMENT_ADDED,
                {
                    "comment_added": True,
                },
            )
        )

    if not history_events:
        db.commit()

    for event_type, details in history_events:
        create_case_history(
            db=db,
            case=case,
            user=user,
            event_type=event_type,
            details=details,
        )

    db.refresh(case)

    return case


def assign_case(
    db: Session,
    *,
    case_id: int,
    assigned_to_user_id: int,
    actor: User,
) -> FraudCaseReview:
    fraud_case = db.get(FraudCaseReview, case_id)

    if fraud_case is None:
        raise FraudCaseNotFoundError(f"Fraud case {case_id} not found.")

    assignee = db.get(User, assigned_to_user_id)

    if assignee is None:
        raise CaseAssigneeNotFoundError(
            f"User {assigned_to_user_id} not found."
        )

    if not assignee.is_active:
        raise InvalidCaseAssigneeError("Inactive users cannot be assigned cases.")

    if assignee.role != UserRole.FRAUD_ANALYST:
        raise InvalidCaseAssigneeError(
            "Cases can only be assigned to fraud analysts."
        )

    if fraud_case.assigned_to_user_id == assignee.id:
        return fraud_case

    previous_assignee = fraud_case.assigned_to_user
    previous_assignee_id = fraud_case.assigned_to_user_id
    previous_username = (
        previous_assignee.username if previous_assignee is not None else None
    )
    event_type = (
        CaseEvent.REASSIGNED
        if previous_assignee_id is not None
        else CaseEvent.ASSIGNED
    )
    audit_action = (
        AuditAction.CASE_REASSIGNED
        if previous_assignee_id is not None
        else AuditAction.CASE_ASSIGNED
    )

    fraud_case.assigned_to_user = assignee

    try:
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=event_type,
            details={
                "old_assignee_user_id": previous_assignee_id,
                "old_assignee_username": previous_username,
                "new_assignee_user_id": assignee.id,
                "new_assignee_username": assignee.username,
            },
            commit=False,
        )
        create_audit_log(
            db=db,
            action=audit_action,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type="fraud_case",
            resource_id=fraud_case.id,
            details={
                "previous_assignee": previous_username,
                "new_assignee": assignee.username,
            },
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(fraud_case)
    return fraud_case


def unassign_case(
    db: Session,
    *,
    case_id: int,
    actor: User,
    reason: str | None = None,
) -> FraudCaseReview:
    fraud_case = db.get(FraudCaseReview, case_id)

    if fraud_case is None:
        raise FraudCaseNotFoundError(f"Fraud case {case_id} not found.")

    if fraud_case.assigned_to_user_id is None:
        return fraud_case

    previous_assignee = fraud_case.assigned_to_user
    previous_assignee_id = fraud_case.assigned_to_user_id
    previous_username = (
        previous_assignee.username if previous_assignee is not None else None
    )
    fraud_case.assigned_to_user = None

    try:
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=CaseEvent.UNASSIGNED,
            details={
                "old_assignee_user_id": previous_assignee_id,
                "old_assignee_username": previous_username,
                "new_assignee_user_id": None,
                "new_assignee_username": None,
                "reason": reason,
            },
            commit=False,
        )
        create_audit_log(
            db=db,
            action=AuditAction.CASE_UNASSIGNED,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type="fraud_case",
            resource_id=fraud_case.id,
            details={
                "previous_assignee": previous_username,
                "new_assignee": None,
            },
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(fraud_case)
    return fraud_case


def get_analyst_workloads(db: Session) -> list[dict[str, int | str | None]]:
    active_non_investigating_statuses = {
        "new",
        "open",
        "assigned",
        "pending_customer",
        "escalated",
        "under_review",
    }
    open_cases = func.sum(
        sql_case(
            (
                FraudCaseReview.case_status.in_(
                    active_non_investigating_statuses
                ),
                1,
            ),
            else_=0,
        )
    )
    investigating_cases = func.sum(
        sql_case(
            (FraudCaseReview.case_status == "investigating", 1),
            else_=0,
        )
    )
    total_active_cases = open_cases + investigating_cases

    rows = (
        db.query(
            User.id.label("analyst_id"),
            User.username,
            User.full_name,
            open_cases.label("open_cases"),
            investigating_cases.label("investigating_cases"),
            total_active_cases.label("total_active_cases"),
        )
        .outerjoin(
            FraudCaseReview,
            FraudCaseReview.assigned_to_user_id == User.id,
        )
        .filter(
            User.role == UserRole.FRAUD_ANALYST,
            User.is_active.is_(True),
        )
        .group_by(User.id, User.username, User.full_name)
        .order_by(total_active_cases.asc(), User.id.asc())
        .all()
    )

    return [
        {
            "analyst_id": row.analyst_id,
            "username": row.username,
            "full_name": row.full_name,
            "open_cases": row.open_cases,
            "investigating_cases": row.investigating_cases,
            "total_active_cases": row.total_active_cases,
        }
        for row in rows
    ]
