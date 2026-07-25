"""
Pydantic schemas for global model explainability and feature insights.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class InsightHealthResponse(BaseModel):
    status: str
    model: str
    samples_used: int
    feature_count: int


class FeatureImportance(BaseModel):
    rank: int = Field(..., ge=1)
    feature: str
    importance: float


class GlobalImportanceResponse(BaseModel):
    generated_at: datetime
    samples: int
    features: list[FeatureImportance]


class FeatureStatistics(BaseModel):
    minimum: float
    maximum: float
    mean: float
    median: float


class FeatureDetailResponse(FeatureStatistics):
    feature: str
    rank: int
    mean_abs_shap: float
    positive_effect: float
    negative_effect: float


class TopFeaturesResponse(BaseModel):
    generated_at: datetime
    direction: str
    features: list[FeatureImportance]
