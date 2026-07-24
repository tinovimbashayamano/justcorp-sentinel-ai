"""REST endpoints for fraud analytics and executive dashboards."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.analytics import (
    AnalyticsHealthResponse,
    AnalyticsPeriod,
    CaseStatusDistributionResponse,
    DashboardSummaryResponse,
    ExecutiveKPIResponse,
    FraudScoreDistributionResponse,
    FraudTrendResponse,
    HighRiskTransactionResponse,
    InvestigatorPerformanceResponse,
    RiskDistributionResponse,
)
from backend.app.services.analytics_service import (
    AnalyticsService,
    AnalyticsValidationError,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


ANALYTICS_ROLES = {
    "admin",
    "analyst",
    "fraud_analyst",
    "risk_manager",
    "manager",
    "auditor",
}


def require_analytics_access(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Allow authorized operational and governance roles."""

    role_value = getattr(current_user.role, "value", current_user.role)

    if str(role_value).lower() not in ANALYTICS_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access analytics.",
        )

    return current_user


def get_analytics_service(
    db: Session = Depends(get_db),
) -> AnalyticsService:
    return AnalyticsService(db)


def translate_validation_error(
    exc: AnalyticsValidationError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.get(
    "/health",
    response_model=AnalyticsHealthResponse,
)
def get_analytics_health(
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsHealthResponse:
    """Return analytics subsystem health and data availability."""

    return service.get_health()


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    high_risk_limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> DashboardSummaryResponse:
    """Return the combined executive dashboard payload."""

    try:
        return service.get_dashboard_summary(
            start_at=start_at,
            end_at=end_at,
            high_risk_limit=high_risk_limit,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc


@router.get(
    "/executive-kpis",
    response_model=ExecutiveKPIResponse,
)
def get_executive_kpis(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> ExecutiveKPIResponse:
    """Return executive fraud and case KPIs."""

    try:
        return service.get_executive_kpis(
            start_at=start_at,
            end_at=end_at,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc


@router.get(
    "/risk-distribution",
    response_model=RiskDistributionResponse,
)
def get_risk_distribution(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> RiskDistributionResponse:
    """Return transaction distribution by fraud-risk level."""

    try:
        return service.get_risk_distribution(
            start_at=start_at,
            end_at=end_at,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc


@router.get(
    "/fraud-score-distribution",
    response_model=FraudScoreDistributionResponse,
)
def get_fraud_score_distribution(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    bucket_count: int = Query(
        default=10,
        ge=2,
        le=50,
    ),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> FraudScoreDistributionResponse:
    """Return a histogram of fraud probabilities."""

    try:
        return service.get_fraud_score_distribution(
            start_at=start_at,
            end_at=end_at,
            bucket_count=bucket_count,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc


@router.get(
    "/fraud-trend",
    response_model=FraudTrendResponse,
)
def get_fraud_trend(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    grouping: AnalyticsPeriod = Query(
        default=AnalyticsPeriod.DAY
    ),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> FraudTrendResponse:
    """Return fraud activity grouped over time."""

    try:
        return service.get_fraud_trend(
            start_at=start_at,
            end_at=end_at,
            grouping=grouping,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc


@router.get(
    "/case-status-distribution",
    response_model=CaseStatusDistributionResponse,
)
def get_case_status_distribution(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> CaseStatusDistributionResponse:
    """Return fraud cases grouped by workflow state."""

    try:
        return service.get_case_status_distribution(
            start_at=start_at,
            end_at=end_at,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc


@router.get(
    "/investigator-performance",
    response_model=InvestigatorPerformanceResponse,
)
def get_investigator_performance(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> InvestigatorPerformanceResponse:
    """Return investigator workload and resolution metrics."""

    try:
        return service.get_investigator_performance(
            start_at=start_at,
            end_at=end_at,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc


@router.get(
    "/high-risk-transactions",
    response_model=HighRiskTransactionResponse,
)
def get_high_risk_transactions(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_analytics_access),
    service: AnalyticsService = Depends(get_analytics_service),
) -> HighRiskTransactionResponse:
    """Return paginated high and critical-risk transactions."""

    try:
        return service.get_high_risk_transactions(
            start_at=start_at,
            end_at=end_at,
            limit=limit,
            offset=offset,
        )
    except AnalyticsValidationError as exc:
        raise translate_validation_error(exc) from exc
