from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FraudCaseCreateRequest(BaseModel):
    fraud_score_record_id: int = Field(..., gt=0)
    case_status: str = "open"
    analyst_decision: str | None = "pending"
    analyst_notes: str | None = None
    reviewed_by: str | None = None


class FraudCaseUpdateRequest(BaseModel):
    case_status: str | None = None
    analyst_decision: str | None = None
    analyst_notes: str | None = None
    reviewed_by: str | None = None


class FraudCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fraud_score_record_id: int
    case_status: str
    analyst_decision: str | None
    analyst_notes: str | None
    reviewed_by: str | None
    created_at: datetime
    updated_at: datetime
