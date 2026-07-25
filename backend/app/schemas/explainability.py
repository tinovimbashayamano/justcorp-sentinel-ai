from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemas.fraud import FeatureQualityWarning


class ExplainabilityRequest(BaseModel):
    """Transaction features and explanation options."""

    transaction_id: str = Field(
        ...,
        min_length=1,
        description="External transaction identifier.",
    )
    features: dict[str, Any] = Field(
        ...,
        description="Transaction feature values used for fraud scoring.",
    )
    top_features: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of SHAP contributions to return.",
    )


class TopFeatureContribution(BaseModel):
    """One ranked local SHAP feature contribution."""

    rank: int = Field(ge=1)
    transformed_feature: str
    source_feature: str
    category: str | None = None
    display_name: str
    feature_value: Any
    shap_value: float
    absolute_shap_value: float = Field(ge=0)
    impact_direction: str
    impact_strength: str


class ExplainabilityResponse(BaseModel):
    """Local explanation for one fraud prediction."""

    model_name: str
    explanation_type: str
    fraud_probability: float = Field(ge=0, le=1)
    fraud_prediction: int = Field(ge=0, le=1)
    fraud_threshold: float = Field(ge=0, le=1)
    risk_band: str
    base_value: float
    top_feature_count: int = Field(ge=0)
    feature_contributions: list[TopFeatureContribution]
    feature_quality: FeatureQualityWarning
    summary: str


class ExplainabilityPrediction(BaseModel):
    """Fraud scoring result returned with an explanation."""

    model_name: str
    fraud_probability: float = Field(ge=0, le=1)
    fraud_prediction: int = Field(ge=0, le=1)
    fraud_threshold: float = Field(ge=0, le=1)
    risk_band: str
    feature_quality: FeatureQualityWarning


class ScoreAndExplainResponse(BaseModel):
    """Combined fraud prediction and local explanation."""

    transaction_id: str
    prediction: ExplainabilityPrediction
    explanation: ExplainabilityResponse


class ExplainabilityHealthResponse(BaseModel):
    """Explainability subsystem readiness and model metadata."""

    status: str
    model_name: str
    pipeline_type: str
    classifier_type: str
    explainer_type: str
    raw_feature_count: int = Field(ge=0)
    transformed_feature_count: int = Field(ge=0)
