from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_user
from backend.app.db.session import get_db
from backend.app.schemas.fraud import (
    FraudModelHealthResponse,
    FraudScoreRequest,
    FraudScoreResponse,
)
from backend.app.schemas.fraud_case import (
    FraudCaseCreateRequest,
    FraudCaseResponse,
    FraudCaseUpdateRequest,
)
from backend.app.schemas.fraud_record import FraudScoreRecordResponse
from backend.app.services.fraud_case_service import (
    create_fraud_case,
    get_fraud_case,
    list_fraud_cases,
    update_fraud_case,
)
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
    dependencies=[
        Depends(get_current_active_user),
    ],
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


@router.post("/cases", response_model=FraudCaseResponse)
def create_case_review(
    request: FraudCaseCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        return create_fraud_case(db=db, request=request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/cases", response_model=list[FraudCaseResponse])
def get_recent_fraud_cases(
    limit: int = Query(default=20, ge=1, le=100),
    case_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return list_fraud_cases(
            db=db,
            limit=limit,
            case_status=case_status,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/cases/{case_id}", response_model=FraudCaseResponse)
def get_case_review(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = get_fraud_case(db=db, case_id=case_id)

    if case is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fraud case {case_id} not found.",
        )

    return case


@router.patch("/cases/{case_id}", response_model=FraudCaseResponse)
def update_case_review(
    case_id: int,
    request: FraudCaseUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        return update_fraud_case(
            db=db,
            case_id=case_id,
            request=request,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
