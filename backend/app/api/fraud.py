from fastapi import APIRouter, HTTPException

from backend.app.schemas.fraud import (
    FraudModelHealthResponse,
    FraudScoreRequest,
    FraudScoreResponse,
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
