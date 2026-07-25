from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.dependencies import (
    AdminAnalystOrAuditor,
    AdminOrAnalyst,
    AnyAuthenticatedUser,
)
from backend.app.db.session import get_db
from backend.app.schemas.fraud import (
    FraudModelHealthResponse,
    FraudScoreRequest,
    FraudScoreResponse,
)
from backend.app.schemas.explainability import (
    ExplainabilityHealthResponse,
    ExplainabilityRequest,
    ExplainabilityResponse,
    ScoreAndExplainResponse,
)
from backend.app.schemas.fraud_case import (
    FraudCaseCreateRequest,
    FraudCaseResponse,
    FraudCaseUpdateRequest,
)
from backend.app.schemas.fraud_record import FraudScoreRecordResponse
from backend.app.services.audit_service import safely_create_audit_log
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
from backend.app.services.explainability_service import (
    explainability_service,
)


router = APIRouter(
    prefix="/api/v1/fraud",
    tags=["Fraud Scoring"],
)


@router.get("/health", response_model=FraudModelHealthResponse)
def fraud_model_health(
    _: AnyAuthenticatedUser,
):
    try:
        return get_model_health()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get(
    "/explainability/health",
    response_model=ExplainabilityHealthResponse,
)
def explainability_health(
    _: AnyAuthenticatedUser,
):
    try:
        return explainability_service.health()
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@router.post(
    "/explain",
    response_model=ExplainabilityResponse,
)
def explain_fraud_transaction(
    payload: ExplainabilityRequest,
    current_user: AdminOrAnalyst,
):
    try:
        return explainability_service.explain(
            payload.features,
            top_features=payload.top_features,
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to explain transaction: {error}",
        ) from error


@router.post(
    "/score-and-explain",
    response_model=ScoreAndExplainResponse,
)
def score_and_explain_fraud_transaction(
    payload: ExplainabilityRequest,
    request: Request,
    current_user: AdminOrAnalyst,
    db: Session = Depends(get_db),
):
    try:
        result = explainability_service.score_and_explain(
            payload.features,
            top_features=payload.top_features,
        )

        safely_create_audit_log(
            db=db,
            action=AuditAction.FRAUD_SCORE,
            status=AuditStatus.SUCCESS,
            user=current_user,
            resource_type="transaction",
            resource_id=payload.transaction_id,
            request=request,
            details={
                "fraud_prediction": result[
                    "prediction"
                ]["fraud_prediction"],
                "fraud_probability": result[
                    "prediction"
                ]["fraud_probability"],
                "explanation_requested": True,
                "requested_top_features": payload.top_features,
            },
        )

        return {
            "transaction_id": payload.transaction_id,
            **result,
        }
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to score and explain transaction: "
                f"{error}"
            ),
        ) from error


@router.post("/score", response_model=FraudScoreResponse)
def score_fraud_transaction(
    payload: FraudScoreRequest,
    request: Request,
    current_user: AdminOrAnalyst,
    db: Session = Depends(get_db),
):
    try:
        result = score_transaction(payload.features)

        safely_create_audit_log(
            db=db,
            action=AuditAction.FRAUD_SCORE,
            status=AuditStatus.SUCCESS,
            user=current_user,
            resource_type="transaction",
            resource_id=payload.transaction_id,
            request=request,
            details={
                "fraud_prediction": result["fraud_prediction"],
                "fraud_probability": result["fraud_probability"],
                "fraud_threshold": result["fraud_threshold"],
            },
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to score transaction: {error}",
        ) from error

    return {
        "transaction_id": payload.transaction_id,
        **result,
    }


@router.post("/score/save", response_model=FraudScoreRecordResponse)
def score_and_save_fraud_transaction(
    payload: FraudScoreRequest,
    request: Request,
    current_user: AdminOrAnalyst,
    db: Session = Depends(get_db),
):
    try:
        result = score_transaction(payload.features)
        record = save_fraud_score_record(
            db=db,
            transaction_id=payload.transaction_id,
            scoring_result=result,
        )

        safely_create_audit_log(
            db=db,
            action=AuditAction.FRAUD_SCORE_SAVE,
            status=AuditStatus.SUCCESS,
            user=current_user,
            resource_type="fraud_score_record",
            resource_id=record.id,
            request=request,
            details={
                "transaction_id": record.transaction_id,
                "fraud_prediction": record.fraud_prediction,
            },
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
    _: AdminAnalystOrAuditor,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_recent_fraud_scores(db=db, limit=limit)


@router.post("/cases", response_model=FraudCaseResponse)
def create_case_review(
    payload: FraudCaseCreateRequest,
    request: Request,
    current_user: AdminOrAnalyst,
    db: Session = Depends(get_db),
):
    try:
        case = create_fraud_case(
            db=db,
            request=payload,
            user=current_user,
        )

        safely_create_audit_log(
            db=db,
            action=AuditAction.CASE_CREATE,
            status=AuditStatus.SUCCESS,
            user=current_user,
            resource_type="fraud_case_review",
            resource_id=case.id,
            request=request,
            details={
                "case_status": case.case_status,
                "priority": case.priority,
                "analyst_decision": case.analyst_decision,
            },
        )

        return case
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/cases", response_model=list[FraudCaseResponse])
def get_recent_fraud_cases(
    _: AdminAnalystOrAuditor,
    limit: int = Query(default=20, ge=1, le=100),
    case_status: str | None = Query(default=None),
    assigned_to_user_id: int | None = Query(default=None, gt=0),
    unassigned: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    if assigned_to_user_id is not None and unassigned:
        raise HTTPException(
            status_code=422,
            detail=(
                "assigned_to_user_id and unassigned cannot both be supplied."
            ),
        )

    try:
        return list_fraud_cases(
            db=db,
            limit=limit,
            case_status=case_status,
            assigned_to_user_id=assigned_to_user_id,
            unassigned=unassigned,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/cases/{case_id}", response_model=FraudCaseResponse)
def get_case_review(
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

    return case


@router.patch("/cases/{case_id}", response_model=FraudCaseResponse)
def update_case_review(
    case_id: int,
    payload: FraudCaseUpdateRequest,
    request: Request,
    current_user: AdminOrAnalyst,
    db: Session = Depends(get_db),
):
    try:
        existing_case = get_fraud_case(db=db, case_id=case_id)
        update_data = payload.model_dump(exclude_unset=True)
        changed_fields = {
            field: {
                "old": getattr(existing_case, field),
                "new": value,
            }
            for field, value in update_data.items()
            if existing_case is not None
            and field != "analyst_notes"
            and getattr(existing_case, field) != value
        }

        updated_case = update_fraud_case(
            db=db,
            case_id=case_id,
            request=payload,
            user=current_user,
        )

        safely_create_audit_log(
            db=db,
            action=AuditAction.CASE_UPDATE,
            status=AuditStatus.SUCCESS,
            user=current_user,
            resource_type="fraud_case_review",
            resource_id=updated_case.id,
            request=request,
            details={
                "changed_fields": changed_fields,
            },
        )

        return updated_case
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
