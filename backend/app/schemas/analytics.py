"""Pydantic contracts for fraud analytics and dashboard reporting."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsPeriod(StrEnum):
    """Supported analytics grouping periods."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class AnalyticsRiskLevel(StrEnum):
    """Normalized fraud-risk classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalyticsDateRange(BaseModel):
    """Resolved date range returned with analytics results."""

    start_at: datetime | None = None
    end_at: datetime | None = None


class ExecutiveKPIResponse(BaseModel):
    """Executive fraud and investigation performance indicators."""

    total_transactions: int = 0
    fraudulent_transactions: int = 0
    legitimate_transactions: int = 0

    fraud_rate: float = 0.0
    average_fraud_score: float = 0.0

    high_risk_transactions: int = 0
    critical_risk_transactions: int = 0

    total_transaction_amount: Decimal = Decimal("0")
    fraudulent_transaction_amount: Decimal = Decimal("0")
    protected_amount: Decimal = Decimal("0")

    total_cases: int = 0
    open_cases: int = 0
    closed_cases: int = 0
    escalated_cases: int = 0

    resolution_rate: float = 0.0
    escalation_rate: float = 0.0

    period: AnalyticsDateRange


class FraudTrendPoint(BaseModel):
    """One time-series fraud analytics bucket."""

    period_start: datetime
    transaction_count: int = 0
    fraudulent_count: int = 0
    legitimate_count: int = 0
    fraud_rate: float = 0.0
    average_fraud_score: float = 0.0
    transaction_amount: Decimal = Decimal("0")
    fraudulent_amount: Decimal = Decimal("0")


class FraudTrendResponse(BaseModel):
    """Fraud time-series response."""

    grouping: AnalyticsPeriod
    period: AnalyticsDateRange
    points: list[FraudTrendPoint] = Field(default_factory=list)


class RiskDistributionItem(BaseModel):
    """Transaction count and value for one risk level."""

    risk_level: AnalyticsRiskLevel
    transaction_count: int = 0
    percentage: float = 0.0
    transaction_amount: Decimal = Decimal("0")
    average_fraud_score: float = 0.0


class RiskDistributionResponse(BaseModel):
    """Fraud-risk distribution response."""

    total_transactions: int = 0
    period: AnalyticsDateRange
    items: list[RiskDistributionItem] = Field(default_factory=list)


class FraudScoreBucket(BaseModel):
    """Histogram bucket for fraud scores."""

    minimum_score: float = Field(ge=0.0, le=1.0)
    maximum_score: float = Field(ge=0.0, le=1.0)
    transaction_count: int = 0
    percentage: float = 0.0


class FraudScoreDistributionResponse(BaseModel):
    """Fraud-score histogram."""

    total_transactions: int = 0
    average_score: float = 0.0
    minimum_score: float = 0.0
    maximum_score: float = 0.0
    period: AnalyticsDateRange
    buckets: list[FraudScoreBucket] = Field(default_factory=list)


class HighRiskTransactionItem(BaseModel):
    """High-risk transaction summary."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    fraud_score: float
    is_fraud: bool
    risk_level: AnalyticsRiskLevel

    transaction_amount: Decimal | None = None
    transaction_date: datetime | None = None
    product_code: str | None = None

    case_id: int | None = None
    case_status: str | None = None


class HighRiskTransactionResponse(BaseModel):
    """Paginated list of high-risk transactions."""

    items: list[HighRiskTransactionItem] = Field(default_factory=list)
    total: int = 0
    limit: int
    offset: int


class CaseStatusDistributionItem(BaseModel):
    """Number of cases in one workflow state."""

    status: str
    case_count: int = 0
    percentage: float = 0.0


class CaseStatusDistributionResponse(BaseModel):
    """Case workflow distribution."""

    total_cases: int = 0
    period: AnalyticsDateRange
    items: list[CaseStatusDistributionItem] = Field(default_factory=list)


class InvestigatorPerformanceItem(BaseModel):
    """Investigator workload and performance indicators."""

    investigator_id: int
    investigator_name: str | None = None

    assigned_cases: int = 0
    open_cases: int = 0
    resolved_cases: int = 0
    escalated_cases: int = 0

    resolution_rate: float = 0.0
    escalation_rate: float = 0.0
    average_resolution_hours: float | None = None


class InvestigatorPerformanceResponse(BaseModel):
    """Investigator performance analytics."""

    period: AnalyticsDateRange
    items: list[InvestigatorPerformanceItem] = Field(default_factory=list)


class FeatureImportanceItem(BaseModel):
    """Aggregated model-explainability feature contribution."""

    feature_name: str
    average_absolute_importance: float = 0.0
    occurrence_count: int = 0
    rank: int = Field(ge=1)


class ExplainabilityAnalyticsResponse(BaseModel):
    """Aggregated explainability analytics."""

    analyzed_predictions: int = 0
    period: AnalyticsDateRange
    features: list[FeatureImportanceItem] = Field(default_factory=list)


class DashboardSummaryResponse(BaseModel):
    """Combined dashboard response for one frontend request."""

    executive_kpis: ExecutiveKPIResponse
    risk_distribution: RiskDistributionResponse
    fraud_trend: FraudTrendResponse
    case_distribution: CaseStatusDistributionResponse
    high_risk_transactions: list[HighRiskTransactionItem] = Field(
        default_factory=list
    )


class AnalyticsHealthResponse(BaseModel):
    """Analytics subsystem health and data-availability response."""

    status: str = "healthy"
    generated_at: datetime
    transaction_records_available: bool
    fraud_scores_available: bool
    case_records_available: bool
    explainability_records_available: bool
    latest_transaction_at: datetime | None = None
    latest_case_at: datetime | None = None


class DailyFraudSummary(BaseModel):
    """Internal repository projection for daily fraud totals."""

    summary_date: date
    total_transactions: int
    fraudulent_transactions: int
    total_amount: Decimal
    fraudulent_amount: Decimal
    average_fraud_score: float


class FraudAggregateData(BaseModel):
    """Internal fraud-score aggregate projection."""

    total_transactions: int = 0
    fraudulent_transactions: int = 0
    average_fraud_score: float = 0.0
    high_risk_transactions: int = 0
    critical_risk_transactions: int = 0


class CaseAggregateData(BaseModel):
    """Internal fraud-case aggregate projection."""

    total_cases: int = 0
    open_cases: int = 0
    closed_cases: int = 0
    escalated_cases: int = 0
