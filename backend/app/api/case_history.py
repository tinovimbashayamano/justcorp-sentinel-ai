from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.dependencies import AdminAnalystOrAuditor
from backend.app.db.session import get_db
from backend.app.schemas.fraud_case import CaseHistoryResponse
from backend.app.services.case_history_service import get_case_history
from backend.app.services.fraud_case_service import get_fraud_case


router = APIRouter(
    prefix="/cases",
    tags=["Case History"],
)


@router.get(
    "/{case_id}/timeline",
    response_model=list[CaseHistoryResponse],
)
def get_case_timeline(
    case_id: int,
    _: AdminAnalystOrAuditor,
    db: Session = Depends(get_db),
):
    case = get_fraud_case(db=db, case_id=case_id)

    if case is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fraud case {case_id} not found.",
        )

    return get_case_history(
        db=db,
        case_id=case_id,
    )
