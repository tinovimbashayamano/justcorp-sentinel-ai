"""Unit tests for analytics repository helpers."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend.app.repositories.analytics_repository import (
    AnalyticsRepository,
    AnalyticsRepositoryError,
)
from backend.app.schemas.analytics import AnalyticsRiskLevel


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.00, AnalyticsRiskLevel.LOW),
        (0.30, AnalyticsRiskLevel.LOW),
        (0.31, AnalyticsRiskLevel.MEDIUM),
        (0.60, AnalyticsRiskLevel.MEDIUM),
        (0.61, AnalyticsRiskLevel.HIGH),
        (0.85, AnalyticsRiskLevel.HIGH),
        (0.86, AnalyticsRiskLevel.CRITICAL),
        (1.00, AnalyticsRiskLevel.CRITICAL),
    ],
)
def test_classify_risk(score, expected):
    assert AnalyticsRepository.classify_risk(score) == expected


def test_classify_risk_accepts_decimal():
    assert (
        AnalyticsRepository.classify_risk(Decimal("0.91"))
        == AnalyticsRiskLevel.CRITICAL
    )


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_classify_risk_rejects_invalid_score(score):
    with pytest.raises(AnalyticsRepositoryError):
        AnalyticsRepository.classify_risk(score)


def test_calculate_percentage():
    result = AnalyticsRepository.calculate_percentage(
        numerator=25,
        denominator=100,
    )

    assert result == 25.0


def test_calculate_percentage_handles_zero_denominator():
    result = AnalyticsRepository.calculate_percentage(
        numerator=25,
        denominator=0,
    )

    assert result == 0.0


def test_calculate_rate():
    result = AnalyticsRepository.calculate_rate(
        numerator=25,
        denominator=100,
    )

    assert result == 0.25


def test_validate_date_range_accepts_valid_dates():
    start_at = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )
    end_at = datetime(
        2026,
        1,
        31,
        tzinfo=timezone.utc,
    )

    resolved_start, resolved_end = AnalyticsRepository.validate_date_range(
        start_at=start_at,
        end_at=end_at,
    )

    assert resolved_start == start_at
    assert resolved_end == end_at


def test_validate_date_range_rejects_reversed_dates():
    start_at = datetime(
        2026,
        2,
        1,
        tzinfo=timezone.utc,
    )
    end_at = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    with pytest.raises(AnalyticsRepositoryError):
        AnalyticsRepository.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )


def test_naive_dates_are_normalized_to_utc():
    value = datetime(2026, 1, 1, 12, 0, 0)

    normalized = AnalyticsRepository.normalize_datetime(value)

    assert normalized is not None
    assert normalized.tzinfo == timezone.utc


def test_numeric_conversion_helpers():
    assert AnalyticsRepository.integer_or_zero(None) == 0
    assert AnalyticsRepository.integer_or_zero(12) == 12

    assert AnalyticsRepository.float_or_zero(None) == 0.0
    assert AnalyticsRepository.float_or_zero("0.75") == 0.75

    assert AnalyticsRepository.decimal_or_zero(None) == Decimal("0")
    assert (
        AnalyticsRepository.decimal_or_zero("100.50")
        == Decimal("100.50")
    )
