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


class FraudCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fraud_score_record_id: int
    case_status: str
    priority: str
    assigned_to: str | None
    closure_reason: str | None
    analyst_decision: str | None
    analyst_notes: str | None
    reviewed_by: str | None
    created_at: datetime
    updated_at: datetime


class CaseHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    user_id: int | None
    actor_username: str | None
    event_type: str
    details: dict[str, Any] | None
    created_at: datetime
