from typing import Any

from pydantic import BaseModel, Field


class FraudScoreRequest(BaseModel):
    transaction_id: str | None = Field(
        default=None,
        description="Optional external transaction identifier.",
    )
    features: dict[str, Any] = Field(
        ...,
        description="Transaction feature values used for fraud scoring.",
    )


class FeatureQualityWarning(BaseModel):
    expected_feature_count: int
    missing_features_count: int
    extra_features_count: int
    missing_features_preview: list[str]
    extra_features_preview: list[str]


class FraudScoreResponse(BaseModel):
    transaction_id: str | None
    model_name: str
    fraud_probability: float
    fraud_prediction: int
    fraud_threshold: float
    risk_band: str
    feature_quality: FeatureQualityWarning


class FraudModelHealthResponse(BaseModel):
    status: str
    model_name: str
    model_path: str
    fraud_threshold: float
    expected_feature_count: int
