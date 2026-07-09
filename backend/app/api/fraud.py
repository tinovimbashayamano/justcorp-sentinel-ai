from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.fraud import (
    FraudModelHealthResponse,
    FraudScoreRequest,
    FraudScoreResponse,
)
from backend.app.schemas.fraud_record import FraudScoreRecordResponse
from backend.app.services.fraud_record_service import (
    list_recent_fraud_scores,
    save_fraud_score_record,
)
from backend.app.services.fraud_scoring_service import (
    get_model_health,
    score_transaction,
)


router = APIRouter(
    prefix="/api/v1/fraud",
    tags=["Fraud Scoring"],
)


@router.get("/health", response_model=FraudModelHealthResponse)
def fraud_model_health():
    try:
        return get_model_health()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/score", response_model=FraudScoreResponse)
def score_fraud_transaction(request: FraudScoreRequest):
    try:
        result = score_transaction(request.features)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to score transaction: {error}",
        ) from error

    return {
        "transaction_id": request.transaction_id,
        **result,
    }


@router.post("/score/save", response_model=FraudScoreRecordResponse)
def score_and_save_fraud_transaction(
    request: FraudScoreRequest,
    db: Session = Depends(get_db),
):
    try:
        result = score_transaction(request.features)
        record = save_fraud_score_record(
            db=db,
            transaction_id=request.transaction_id,
            scoring_result=result,
        )

        return record
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to score and save transaction: {error}",
        ) from error


@router.get("/scores", response_model=list[FraudScoreRecordResponse])
def get_recent_fraud_scores(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_recent_fraud_scores(db=db, limit=limit)
