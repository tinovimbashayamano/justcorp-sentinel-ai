"""Unit tests for analytics service transformations and validation."""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.app.repositories.analytics_repository import AnalyticsRepository
from backend.app.schemas.analytics import (
    AnalyticsPeriod,
    AnalyticsRiskLevel,
)
from backend.app.services.analytics_service import (
    AnalyticsService,
    AnalyticsValidationError,
)


@pytest.fixture
def repository() -> MagicMock:
    """Return a repository mock that preserves shared helper behavior."""

    mocked = MagicMock(spec=AnalyticsRepository)
    mocked.validate_date_range.side_effect = (
        lambda *, start_at=None, end_at=None: (start_at, end_at)
    )
    mocked.calculate_percentage.side_effect = (
        AnalyticsRepository.calculate_percentage
    )
    return mocked


@pytest.fixture
def service(repository: MagicMock) -> AnalyticsService:
    return AnalyticsService(
        db=MagicMock(),
        repository=repository,
    )


def test_executive_kpis_include_counts_and_zero_financial_metrics(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_fraud_aggregate.return_value = {
        "total_transactions": 10,
        "fraudulent_transactions": 4,
        "average_fraud_score": 0.4567894,
        "high_risk_transactions": 3,
        "critical_risk_transactions": 1,
    }
    repository.get_case_aggregate.return_value = {
        "total_cases": 5,
        "open_cases": 2,
        "closed_cases": 2,
        "escalated_cases": 1,
    }

    result = service.get_executive_kpis()

    assert result.total_transactions == 10
    assert result.fraudulent_transactions == 4
    assert result.legitimate_transactions == 6
    assert result.fraud_rate == 40.0
    assert result.average_fraud_score == 0.456789
    assert result.total_cases == 5
    assert result.resolution_rate == 40.0
    assert result.escalation_rate == 20.0
    assert result.total_transaction_amount == Decimal("0")
    assert result.fraudulent_transaction_amount == Decimal("0")
    assert result.protected_amount == Decimal("0")


def test_risk_distribution_fills_missing_bands(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_risk_distribution.return_value = [
        {
            "risk_level": "high",
            "transaction_count": 3,
            "average_fraud_score": 0.75,
        },
        {
            "risk_level": "critical",
            "transaction_count": 1,
            "average_fraud_score": 0.95,
        },
    ]

    result = service.get_risk_distribution()
    items = {item.risk_level: item for item in result.items}

    assert result.total_transactions == 4
    assert set(items) == set(AnalyticsRiskLevel)
    assert items[AnalyticsRiskLevel.HIGH].transaction_count == 3
    assert items[AnalyticsRiskLevel.HIGH].percentage == 75.0
    assert items[AnalyticsRiskLevel.CRITICAL].percentage == 25.0
    assert items[AnalyticsRiskLevel.LOW].transaction_count == 0
    assert all(
        item.transaction_amount == Decimal("0")
        for item in result.items
    )


def test_score_distribution_builds_requested_histogram(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_fraud_score_values.return_value = [
        0.0,
        0.24,
        0.25,
        0.74,
        1.0,
    ]

    result = service.get_fraud_score_distribution(bucket_count=4)

    assert result.total_transactions == 5
    assert result.average_score == 0.446
    assert result.minimum_score == 0.0
    assert result.maximum_score == 1.0
    assert len(result.buckets) == 4
    assert [
        bucket.transaction_count
        for bucket in result.buckets
    ] == [2, 1, 1, 1]
    assert result.buckets[-1].maximum_score == 1.0


@pytest.mark.parametrize("bucket_count", [1, 51])
def test_score_distribution_rejects_invalid_bucket_count(
    service: AnalyticsService,
    bucket_count: int,
):
    with pytest.raises(
        AnalyticsValidationError,
        match="between 2 and 50",
    ):
        service.get_fraud_score_distribution(
            bucket_count=bucket_count,
        )


def test_daily_trend_calculates_rates_and_zero_amounts(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_daily_fraud_trend.return_value = [
        {
            "period_start": date(2026, 7, 24),
            "transaction_count": 8,
            "fraudulent_count": 2,
            "average_fraud_score": 0.375,
        }
    ]

    result = service.get_fraud_trend()
    point = result.points[0]

    assert result.grouping == AnalyticsPeriod.DAY
    assert point.period_start == datetime(
        2026,
        7,
        24,
        tzinfo=timezone.utc,
    )
    assert point.legitimate_count == 6
    assert point.fraud_rate == 25.0
    assert point.transaction_amount == Decimal("0")
    assert point.fraudulent_amount == Decimal("0")


def test_trend_rejects_unsupported_grouping(
    service: AnalyticsService,
):
    with pytest.raises(
        AnalyticsValidationError,
        match="daily fraud-trend grouping only",
    ):
        service.get_fraud_trend(
            grouping=AnalyticsPeriod.MONTH,
        )


def test_case_distribution_calculates_percentages(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_case_status_distribution.return_value = [
        {"status": "open", "case_count": 3},
        {"status": "closed", "case_count": 1},
    ]

    result = service.get_case_status_distribution()

    assert result.total_cases == 4
    assert result.items[0].status == "open"
    assert result.items[0].percentage == 75.0
    assert result.items[1].percentage == 25.0


def test_investigator_performance_calculates_rates(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_investigator_performance.return_value = [
        {
            "investigator_id": 7,
            "investigator_name": "analyst-one",
            "assigned_cases": 5,
            "open_cases": 2,
            "resolved_cases": 3,
            "escalated_cases": 1,
            "average_resolution_hours": 12.5,
        }
    ]

    result = service.get_investigator_performance()
    item = result.items[0]

    assert item.investigator_id == 7
    assert item.assigned_cases == 5
    assert item.resolution_rate == 60.0
    assert item.escalation_rate == 20.0
    assert item.average_resolution_hours == 12.5


def test_high_risk_transactions_map_records_and_missing_financial_data(
    service: AnalyticsService,
    repository: MagicMock,
):
    created_at = datetime(2026, 7, 24, tzinfo=timezone.utc)
    record = SimpleNamespace(
        id=11,
        transaction_id="TX-11",
        fraud_probability=0.91,
        fraud_prediction=1,
        risk_band="critical",
        created_at=created_at,
    )
    fraud_case = SimpleNamespace(
        id=22,
        case_status="open",
    )
    repository.get_high_risk_transactions.return_value = (
        [record],
        1,
    )
    repository.get_case_by_score_record_ids.return_value = {
        11: fraud_case
    }

    result = service.get_high_risk_transactions(
        limit=10,
        offset=0,
    )
    item = result.items[0]

    assert result.total == 1
    assert result.limit == 10
    assert result.offset == 0
    assert item.transaction_id == "TX-11"
    assert item.risk_level == AnalyticsRiskLevel.CRITICAL
    assert item.case_id == 22
    assert item.case_status == "open"
    assert item.transaction_amount is None
    assert item.product_code is None


def test_health_exposes_repository_availability(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_data_availability.return_value = {
        "transaction_records_available": True,
        "fraud_scores_available": True,
        "case_records_available": False,
        "explainability_records_available": False,
        "latest_transaction_at": None,
        "latest_case_at": None,
    }

    result = service.get_health()

    assert result.status == "healthy"
    assert result.transaction_records_available is True
    assert result.fraud_scores_available is True
    assert result.case_records_available is False
    assert result.explainability_records_available is False
    assert result.generated_at.tzinfo == timezone.utc


def test_dashboard_summary_combines_service_sections(
    service: AnalyticsService,
    repository: MagicMock,
):
    repository.get_fraud_aggregate.return_value = {
        "total_transactions": 0,
        "fraudulent_transactions": 0,
        "average_fraud_score": 0.0,
        "high_risk_transactions": 0,
        "critical_risk_transactions": 0,
    }
    repository.get_case_aggregate.return_value = {
        "total_cases": 0,
        "open_cases": 0,
        "closed_cases": 0,
        "escalated_cases": 0,
    }
    repository.get_risk_distribution.return_value = []
    repository.get_daily_fraud_trend.return_value = []
    repository.get_case_status_distribution.return_value = []
    repository.get_high_risk_transactions.return_value = ([], 0)
    repository.get_case_by_score_record_ids.return_value = {}

    result = service.get_dashboard_summary(high_risk_limit=5)

    assert result.executive_kpis.total_transactions == 0
    assert result.risk_distribution.total_transactions == 0
    assert result.fraud_trend.points == []
    assert result.case_distribution.total_cases == 0
    assert result.high_risk_transactions == []
    repository.get_high_risk_transactions.assert_called_once_with(
        start_at=None,
        end_at=None,
        limit=5,
        offset=0,
    )
