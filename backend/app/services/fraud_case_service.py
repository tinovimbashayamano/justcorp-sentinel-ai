from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.schemas.fraud_case import (
    FraudCaseCreateRequest,
    FraudCaseUpdateRequest,
)


VALID_CASE_STATUSES = {
    "open",
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


def create_fraud_case(
    db: Session,
    request: FraudCaseCreateRequest,
) -> FraudCaseReview:
    score_record = db.get(FraudScoreRecord, request.fraud_score_record_id)

    if score_record is None:
        raise ValueError(
            f"Fraud score record {request.fraud_score_record_id} does not exist."
        )

    validate_case_status(request.case_status)
    validate_analyst_decision(request.analyst_decision)

    case = FraudCaseReview(
        fraud_score_record_id=request.fraud_score_record_id,
        case_status=request.case_status,
        analyst_decision=request.analyst_decision,
        analyst_notes=request.analyst_notes,
        reviewed_by=request.reviewed_by,
    )

    db.add(case)
    db.commit()
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
) -> FraudCaseReview:
    case = db.get(FraudCaseReview, case_id)

    if case is None:
        raise ValueError(f"Fraud case {case_id} does not exist.")

    update_data = request.model_dump(exclude_unset=True)

    if "case_status" in update_data and update_data["case_status"] is not None:
        validate_case_status(update_data["case_status"])

    if (
        "analyst_decision" in update_data
        and update_data["analyst_decision"] is not None
    ):
        validate_analyst_decision(update_data["analyst_decision"])

    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)

    return case
