from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.dependencies import AdminUser
from backend.app.db.session import get_db
from backend.app.schemas.fraud_case import (
    AnalystWorkloadResponse,
    CaseAssignmentRequest,
    FraudCaseResponse,
)
from backend.app.services.fraud_case_service import (
    CaseAssigneeNotFoundError,
    FraudCaseNotFoundError,
    InvalidCaseAssigneeError,
    assign_case,
    get_analyst_workloads,
    unassign_case,
)


router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Case Assignments"],
)


@router.get(
    "/assignments/workload",
    response_model=list[AnalystWorkloadResponse],
)
def analyst_workload(
    _: AdminUser,
    db: Session = Depends(get_db),
):
    return get_analyst_workloads(db)


@router.patch(
    "/{case_id}/assignment",
    response_model=FraudCaseResponse,
)
def assign_or_reassign_case(
    case_id: int,
    payload: CaseAssignmentRequest,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        return assign_case(
            db,
            case_id=case_id,
            assigned_to_user_id=payload.assigned_to_user_id,
            actor=current_user,
        )
    except (FraudCaseNotFoundError, CaseAssigneeNotFoundError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidCaseAssigneeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete(
    "/{case_id}/assignment",
    response_model=FraudCaseResponse,
)
def remove_case_assignment(
    case_id: int,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        return unassign_case(
            db,
            case_id=case_id,
            actor=current_user,
            reason="manual_unassignment",
        )
    except FraudCaseNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
