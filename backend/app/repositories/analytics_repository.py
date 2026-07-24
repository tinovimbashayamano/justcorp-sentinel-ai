"""Read-only SQLAlchemy repository for fraud analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Sequence

from sqlalchemy import (
    case,
    desc,
    func,
    select,
)
from sqlalchemy.orm import Session

from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User
from backend.app.schemas.analytics import AnalyticsRiskLevel


class AnalyticsRepositoryError(RuntimeError):
    """Raised when an analytics query cannot be completed."""


class AnalyticsRepository:
    """Read-only aggregation repository for dashboard analytics."""

    LOW_RISK_MAXIMUM = 0.30
    MEDIUM_RISK_MAXIMUM = 0.60
    HIGH_RISK_MAXIMUM = 0.85

    CLOSED_CASE_STATUSES = {
        "closed",
        "confirmed_fraud",
        "false_positive",
    }

    OPEN_CASE_STATUSES = {
        "open",
        "under_review",
    }

    HIGH_RISK_BANDS = {
        "high",
        "critical",
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # General helpers
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_datetime(
        value: datetime | None,
    ) -> datetime | None:
        """Normalize a datetime value to UTC."""

        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @classmethod
    def validate_date_range(
        cls,
        *,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        """Validate and normalize an analytics date range."""

        normalized_start = cls.normalize_datetime(start_at)
        normalized_end = cls.normalize_datetime(end_at)

        if (
            normalized_start is not None
            and normalized_end is not None
            and normalized_start > normalized_end
        ):
            raise AnalyticsRepositoryError(
                "Analytics start date cannot be later than the end date."
            )

        return normalized_start, normalized_end

    @classmethod
    def classify_risk(
        cls,
        fraud_score: float | Decimal | None,
    ) -> AnalyticsRiskLevel:
        """Convert a probability into a normalized risk level."""

        if fraud_score is None:
            return AnalyticsRiskLevel.LOW

        score = float(fraud_score)

        if score < 0.0 or score > 1.0:
            raise AnalyticsRepositoryError(
                "Fraud score must be between 0 and 1."
            )

        if score <= cls.LOW_RISK_MAXIMUM:
            return AnalyticsRiskLevel.LOW

        if score <= cls.MEDIUM_RISK_MAXIMUM:
            return AnalyticsRiskLevel.MEDIUM

        if score <= cls.HIGH_RISK_MAXIMUM:
            return AnalyticsRiskLevel.HIGH

        return AnalyticsRiskLevel.CRITICAL

    @staticmethod
    def calculate_percentage(
        numerator: int | float | Decimal,
        denominator: int | float | Decimal,
    ) -> float:
        denominator_value = float(denominator)

        if denominator_value == 0:
            return 0.0

        return round(
            float(numerator) / denominator_value * 100,
            2,
        )

    @staticmethod
    def calculate_rate(
        numerator: int | float | Decimal,
        denominator: int | float | Decimal,
    ) -> float:
        denominator_value = float(denominator)

        if denominator_value == 0:
            return 0.0

        return round(
            float(numerator) / denominator_value,
            6,
        )

    @staticmethod
    def decimal_or_zero(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")

        if isinstance(value, Decimal):
            return value

        return Decimal(str(value))

    @staticmethod
    def float_or_zero(value: Any) -> float:
        if value is None:
            return 0.0

        return float(value)

    @staticmethod
    def integer_or_zero(value: Any) -> int:
        if value is None:
            return 0

        return int(value)

    @staticmethod
    def _apply_date_filter(
        statement,
        *,
        column,
        start_at: datetime | None,
        end_at: datetime | None,
    ):
        if start_at is not None:
            statement = statement.where(column >= start_at)

        if end_at is not None:
            statement = statement.where(column <= end_at)

        return statement

    # ------------------------------------------------------------------
    # Fraud-score aggregates
    # ------------------------------------------------------------------

    def get_fraud_aggregate(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Return executive fraud-score aggregates."""

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = select(
            func.count(FraudScoreRecord.id).label(
                "total_transactions"
            ),
            func.coalesce(
                func.sum(
                    case(
                        (
                            FraudScoreRecord.fraud_prediction == 1,
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("fraudulent_transactions"),
            func.coalesce(
                func.avg(FraudScoreRecord.fraud_probability),
                0.0,
            ).label("average_fraud_score"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            FraudScoreRecord.risk_band.in_(
                                ["high", "critical"]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("high_risk_transactions"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            FraudScoreRecord.risk_band == "critical",
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("critical_risk_transactions"),
        )

        statement = self._apply_date_filter(
            statement,
            column=FraudScoreRecord.created_at,
            start_at=start_at,
            end_at=end_at,
        )

        row = self.db.execute(statement).one()

        return {
            "total_transactions": self.integer_or_zero(
                row.total_transactions
            ),
            "fraudulent_transactions": self.integer_or_zero(
                row.fraudulent_transactions
            ),
            "average_fraud_score": self.float_or_zero(
                row.average_fraud_score
            ),
            "high_risk_transactions": self.integer_or_zero(
                row.high_risk_transactions
            ),
            "critical_risk_transactions": self.integer_or_zero(
                row.critical_risk_transactions
            ),
        }

    def get_risk_distribution(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return transaction counts grouped by persisted risk band."""

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = (
            select(
                FraudScoreRecord.risk_band.label("risk_level"),
                func.count(FraudScoreRecord.id).label(
                    "transaction_count"
                ),
                func.coalesce(
                    func.avg(FraudScoreRecord.fraud_probability),
                    0.0,
                ).label("average_fraud_score"),
            )
            .group_by(FraudScoreRecord.risk_band)
            .order_by(FraudScoreRecord.risk_band)
        )

        statement = self._apply_date_filter(
            statement,
            column=FraudScoreRecord.created_at,
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.db.execute(statement).all()

        return [
            {
                "risk_level": row.risk_level or "low",
                "transaction_count": self.integer_or_zero(
                    row.transaction_count
                ),
                "average_fraud_score": self.float_or_zero(
                    row.average_fraud_score
                ),
            }
            for row in rows
        ]

    def get_fraud_score_values(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[float]:
        """Return persisted fraud probabilities."""

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = select(
            FraudScoreRecord.fraud_probability
        ).where(
            FraudScoreRecord.fraud_probability.is_not(None)
        )

        statement = self._apply_date_filter(
            statement,
            column=FraudScoreRecord.created_at,
            start_at=start_at,
            end_at=end_at,
        )

        values = self.db.scalars(statement).all()

        return [float(value) for value in values]

    def get_daily_fraud_trend(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return fraud-score aggregates grouped by calendar day."""

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        date_bucket = func.date(FraudScoreRecord.created_at)

        statement = (
            select(
                date_bucket.label("period_start"),
                func.count(FraudScoreRecord.id).label(
                    "transaction_count"
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                FraudScoreRecord.fraud_prediction == 1,
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("fraudulent_count"),
                func.coalesce(
                    func.avg(
                        FraudScoreRecord.fraud_probability
                    ),
                    0.0,
                ).label("average_fraud_score"),
            )
            .group_by(date_bucket)
            .order_by(date_bucket)
        )

        statement = self._apply_date_filter(
            statement,
            column=FraudScoreRecord.created_at,
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.db.execute(statement).all()

        return [
            {
                "period_start": row.period_start,
                "transaction_count": self.integer_or_zero(
                    row.transaction_count
                ),
                "fraudulent_count": self.integer_or_zero(
                    row.fraudulent_count
                ),
                "average_fraud_score": self.float_or_zero(
                    row.average_fraud_score
                ),
            }
            for row in rows
        ]

    def get_high_risk_transactions(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Any], int]:
        """Return high and critical risk transactions."""

        if limit < 1 or limit > 100:
            raise AnalyticsRepositoryError(
                "High-risk transaction limit must be between 1 and 100."
            )

        if offset < 0:
            raise AnalyticsRepositoryError(
                "High-risk transaction offset cannot be negative."
            )

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        filters = [
            FraudScoreRecord.risk_band.in_(["high", "critical"])
        ]

        if start_at is not None:
            filters.append(FraudScoreRecord.created_at >= start_at)

        if end_at is not None:
            filters.append(FraudScoreRecord.created_at <= end_at)

        count_statement = select(
            func.count(FraudScoreRecord.id)
        ).where(*filters)

        total = self.db.scalar(count_statement) or 0

        statement = (
            select(FraudScoreRecord)
            .where(*filters)
            .order_by(
                desc(FraudScoreRecord.fraud_probability),
                desc(FraudScoreRecord.created_at),
            )
            .limit(limit)
            .offset(offset)
        )

        records = self.db.scalars(statement).all()

        return records, int(total)

    # ------------------------------------------------------------------
    # Case aggregates
    # ------------------------------------------------------------------

    def get_case_aggregate(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> dict[str, int]:
        """Return aggregate case workflow counts."""

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = select(
            func.count(FraudCaseReview.id).label("total_cases"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            FraudCaseReview.case_status.in_(
                                list(self.OPEN_CASE_STATUSES)
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("open_cases"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            FraudCaseReview.case_status.in_(
                                list(self.CLOSED_CASE_STATUSES)
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("closed_cases"),
        )

        statement = self._apply_date_filter(
            statement,
            column=FraudCaseReview.created_at,
            start_at=start_at,
            end_at=end_at,
        )

        row = self.db.execute(statement).one()

        return {
            "total_cases": self.integer_or_zero(row.total_cases),
            "open_cases": self.integer_or_zero(row.open_cases),
            "closed_cases": self.integer_or_zero(row.closed_cases),
            # No explicit escalation field currently exists.
            "escalated_cases": 0,
        }

    def get_case_status_distribution(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return case counts grouped by workflow status."""

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = (
            select(
                FraudCaseReview.case_status.label("status"),
                func.count(FraudCaseReview.id).label(
                    "case_count"
                ),
            )
            .group_by(FraudCaseReview.case_status)
            .order_by(FraudCaseReview.case_status)
        )

        statement = self._apply_date_filter(
            statement,
            column=FraudCaseReview.created_at,
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.db.execute(statement).all()

        return [
            {
                "status": row.status,
                "case_count": self.integer_or_zero(
                    row.case_count
                ),
            }
            for row in rows
        ]

    def get_investigator_performance(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return workload statistics for assigned investigators."""

        start_at, end_at = self.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        statement = (
            select(
                FraudCaseReview.assigned_to_user_id.label(
                    "investigator_id"
                ),
                User.username.label("investigator_name"),
                func.count(FraudCaseReview.id).label(
                    "assigned_cases"
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                FraudCaseReview.case_status.in_(
                                    list(self.OPEN_CASE_STATUSES)
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("open_cases"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                FraudCaseReview.case_status.in_(
                                    list(self.CLOSED_CASE_STATUSES)
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("resolved_cases"),
            )
            .outerjoin(
                User,
                User.id == FraudCaseReview.assigned_to_user_id,
            )
            .where(FraudCaseReview.assigned_to_user_id.is_not(None))
            .group_by(
                FraudCaseReview.assigned_to_user_id,
                User.username,
            )
            .order_by(desc(func.count(FraudCaseReview.id)))
        )

        statement = self._apply_date_filter(
            statement,
            column=FraudCaseReview.created_at,
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.db.execute(statement).all()

        return [
            {
                "investigator_id": row.investigator_id,
                "investigator_name": row.investigator_name,
                "assigned_cases": self.integer_or_zero(
                    row.assigned_cases
                ),
                "open_cases": self.integer_or_zero(row.open_cases),
                "resolved_cases": self.integer_or_zero(
                    row.resolved_cases
                ),
                "escalated_cases": 0,
                "average_resolution_hours": None,
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # High-risk case lookup
    # ------------------------------------------------------------------

    def get_case_by_score_record_ids(
        self,
        score_record_ids: list[int],
    ) -> dict[int, FraudCaseReview]:
        """Return cases indexed by fraud-score record ID."""

        if not score_record_ids:
            return {}

        statement = select(FraudCaseReview).where(
            FraudCaseReview.fraud_score_record_id.in_(
                score_record_ids
            )
        )

        cases = self.db.scalars(statement).all()

        return {
            fraud_case.fraud_score_record_id: fraud_case
            for fraud_case in cases
        }

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def get_data_availability(self) -> dict[str, Any]:
        """Return analytics source availability and latest timestamps."""

        transaction_count = self.db.scalar(
            select(func.count(FraudScoreRecord.id))
        ) or 0

        score_count = self.db.scalar(
            select(func.count(FraudScoreRecord.id)).where(
                FraudScoreRecord.fraud_probability.is_not(None)
            )
        ) or 0

        case_count = self.db.scalar(
            select(func.count(FraudCaseReview.id))
        ) or 0

        latest_transaction_at = self.db.scalar(
            select(func.max(FraudScoreRecord.created_at))
        )

        latest_case_at = self.db.scalar(
            select(func.max(FraudCaseReview.created_at))
        )

        return {
            "transaction_records_available": transaction_count > 0,
            "fraud_scores_available": score_count > 0,
            "case_records_available": case_count > 0,
            # SHAP values are not currently stored in a queryable table.
            "explainability_records_available": False,
            "latest_transaction_at": latest_transaction_at,
            "latest_case_at": latest_case_at,
        }
