from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.case_history import CaseEvent
from backend.app.models.case_history import CaseHistory
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.user import User


def create_case_history(
    db: Session,
    *,
    case: FraudCaseReview,
    user: User | None,
    event_type: CaseEvent | str,
    details: dict[str, Any] | None = None,
    commit: bool = True,
) -> CaseHistory:
    history_entry = CaseHistory(
        case_id=case.id,
        user_id=user.id if user else None,
        actor_username=user.username if user else None,
        event_type=str(event_type),
        details=details,
    )

    db.add(history_entry)

    if commit:
        db.commit()
        db.refresh(history_entry)
    else:
        db.flush()

    return history_entry


def get_case_history(
    db: Session,
    case_id: int,
) -> list[CaseHistory]:
    return (
        db.query(CaseHistory)
        .filter(CaseHistory.case_id == case_id)
        .order_by(
            CaseHistory.created_at.asc(),
            CaseHistory.id.asc(),
        )
        .all()
    )
