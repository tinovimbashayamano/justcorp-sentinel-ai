from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FraudCaseCreateRequest(BaseModel):
    fraud_score_record_id: int = Field(..., gt=0)
    case_status: str = "open"
    priority: str = "medium"
    assigned_to: str | None = None
    closure_reason: str | None = None
    analyst_decision: str | None = "pending"
    analyst_notes: str | None = None
    reviewed_by: str | None = None


class FraudCaseUpdateRequest(BaseModel):
    case_status: str | None = None
    priority: str | None = None
    assigned_to: str | None = None
    closure_reason: str | None = None
    analyst_decision: str | None = None
    analyst_notes: str | None = None
    reviewed_by: str | None = None


class CaseAssignmentRequest(BaseModel):
    assigned_to_user_id: int = Field(gt=0)


class CaseUnassignmentRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class FraudCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fraud_score_record_id: int
    case_status: str
    priority: str
    assigned_to: str | None
    assigned_to_user_id: int | None = None
    assigned_to_username: str | None = None
    closure_reason: str | None
    analyst_decision: str | None
    analyst_notes: str | None
    reviewed_by: str | None
    created_at: datetime
    updated_at: datetime


class AnalystWorkloadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analyst_id: int
    username: str
    full_name: str | None = None
    open_cases: int
    investigating_cases: int
    total_active_cases: int


class CaseHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    user_id: int | None
    actor_username: str | None
    event_type: str
    details: dict[str, Any] | None
    created_at: datetime
