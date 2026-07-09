from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FraudScoreRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str | None
    model_name: str
    fraud_probability: float
    fraud_prediction: int
    fraud_threshold: float
    risk_band: str
    feature_quality: dict[str, Any]
    created_at: datetime
