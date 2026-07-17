from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.core.case_history import CaseEvent
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User
from backend.app.schemas.fraud_case import (
    FraudCaseCreateRequest,
    FraudCaseUpdateRequest,
)
from backend.app.services.case_history_service import create_case_history


VALID_CASE_STATUSES = {
    "open",
    "investigating",
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
) -> list[FraudCaseReview]:
    query = db.query(FraudCaseReview)

    if case_status is not None:
        validate_case_status(case_status)
        query = query.filter(FraudCaseReview.case_status == case_status)

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
