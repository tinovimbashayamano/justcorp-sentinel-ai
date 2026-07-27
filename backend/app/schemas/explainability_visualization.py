"""Schemas for explainability visualization data and report exports."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class VisualizationRequest(BaseModel):
    """Features and options used to visualize a local explanation."""

    transaction_id: str = Field(min_length=1, max_length=128)
    features: dict[str, Any]
    top_features: int = Field(default=10, ge=1, le=30)


class PlotPoint(BaseModel):
    """One feature contribution in a local visualization."""

    feature: str
    feature_value: Any | None = None
    shap_value: float
    absolute_impact: float
    direction: Literal[
        "increases_fraud_risk",
        "reduces_fraud_risk",
        "neutral",
    ]


class LocalVisualizationData(BaseModel):
    """Plot-ready data for one transaction explanation."""

    transaction_id: str
    prediction: int
    fraud_probability: float = Field(ge=0, le=1)
    risk_band: str
    base_value: float
    summary: str
    points: list[PlotPoint]


class PlotImageResponse(BaseModel):
    """Base64-encoded local explanation plot."""

    transaction_id: str
    plot_type: Literal["waterfall", "force"]
    media_type: str = "image/png"
    image_base64: str


class GlobalPlotPoint(BaseModel):
    """One ranked feature in a global visualization."""

    rank: int = Field(ge=1)
    feature: str
    importance: float = Field(ge=0)


class GlobalVisualizationData(BaseModel):
    """Plot-ready global feature importance data."""

    plot_type: Literal["summary_bar"] = "summary_bar"
    samples: int
    generated_at: str
    features: list[GlobalPlotPoint]


class GlobalPlotImageResponse(BaseModel):
    """Base64-encoded global feature importance plot."""

    plot_type: Literal["summary_bar"] = "summary_bar"
    media_type: str = "image/png"
    image_base64: str


class DependencePoint(BaseModel):
    """One feature-value and SHAP-value pair."""

    feature_value: float | str | None
    shap_value: float


class DependencePlotResponse(BaseModel):
    """Plot-ready SHAP dependence data for a feature."""

    feature: str
    points: list[DependencePoint]
    sample_count: int


class InvestigationReportRequest(VisualizationRequest):
    """Options for an investigation explainability report."""

    case_id: int | None = Field(default=None, ge=1)
    analyst_notes: str | None = Field(default=None, max_length=5000)
    include_global_context: bool = True


class InvestigationReportResponse(BaseModel):
    """Base64-encoded explainability report."""

    transaction_id: str
    case_id: int | None
    report_format: Literal["html", "pdf"]
    media_type: str
    filename: str
    content_base64: str


class VisualizationHealthResponse(BaseModel):
    """Readiness of visualization dependencies and source services."""

    status: str
    local_explainability: str
    global_explainability: str
    plotting_backend: str
    supported_plots: list[str]
    supported_exports: list[str]
