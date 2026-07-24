"""Business logic for executive and fraud dashboard analytics."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from statistics import mean

from sqlalchemy.orm import Session

from backend.app.repositories.analytics_repository import (
    AnalyticsRepository,
    AnalyticsRepositoryError,
)
from backend.app.schemas.analytics import (
    AnalyticsDateRange,
    AnalyticsHealthResponse,
    AnalyticsPeriod,
    AnalyticsRiskLevel,
    CaseStatusDistributionItem,
    CaseStatusDistributionResponse,
    DashboardSummaryResponse,
    ExecutiveKPIResponse,
    FraudScoreBucket,
    FraudScoreDistributionResponse,
    FraudTrendPoint,
    FraudTrendResponse,
    HighRiskTransactionItem,
    HighRiskTransactionResponse,
    InvestigatorPerformanceItem,
    InvestigatorPerformanceResponse,
    RiskDistributionItem,
    RiskDistributionResponse,
)


class AnalyticsServiceError(RuntimeError):
    """Base analytics service error."""


class AnalyticsValidationError(AnalyticsServiceError):
    """Raised when analytics input is invalid."""


class AnalyticsService:
    """Build dashboard-ready analytics from repository aggregates."""

    DEFAULT_HISTOGRAM_BUCKETS = 10

    def __init__(
        self,
        db: Session,
        repository: AnalyticsRepository | None = None,
    ) -> None:
        self.db = db
        self.repository = repository or AnalyticsRepository(db)

    @staticmethod
    def _period(
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> AnalyticsDateRange:
        return AnalyticsDateRange(
            start_at=start_at,
            end_at=end_at,
        )

    @staticmethod
    def _to_datetime(value) -> datetime:
        """Convert SQL date output into a timezone-aware datetime."""

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)

            return value.astimezone(timezone.utc)

        if isinstance(value, date):
            return datetime.combine(
                value,
                time.min,
                tzinfo=timezone.utc,
            )

        parsed = datetime.fromisoformat(str(value))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed

    @staticmethod
    def _normalize_risk_level(
        value: str | None,
    ) -> AnalyticsRiskLevel:
        normalized = (value or "low").strip().lower()

        try:
            return AnalyticsRiskLevel(normalized)
        except ValueError:
            return AnalyticsRiskLevel.LOW

    def get_executive_kpis(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> ExecutiveKPIResponse:
        """Build executive-level fraud and case KPIs."""

        try:
            start_at, end_at = self.repository.validate_date_range(
                start_at=start_at,
                end_at=end_at,
            )

            fraud = self.repository.get_fraud_aggregate(
                start_at=start_at,
                end_at=end_at,
            )

            cases = self.repository.get_case_aggregate(
                start_at=start_at,
                end_at=end_at,
            )

        except AnalyticsRepositoryError as exc:
            raise AnalyticsValidationError(str(exc)) from exc

        total_transactions = fraud["total_transactions"]
        fraudulent_transactions = fraud["fraudulent_transactions"]
        legitimate_transactions = max(
            total_transactions - fraudulent_transactions,
            0,
        )

        total_cases = cases["total_cases"]
        closed_cases = cases["closed_cases"]
        escalated_cases = cases["escalated_cases"]

        return ExecutiveKPIResponse(
            total_transactions=total_transactions,
            fraudulent_transactions=fraudulent_transactions,
            legitimate_transactions=legitimate_transactions,
            fraud_rate=self.repository.calculate_percentage(
                fraudulent_transactions,
                total_transactions,
            ),
            average_fraud_score=round(
                fraud["average_fraud_score"],
                6,
            ),
            high_risk_transactions=fraud[
                "high_risk_transactions"
            ],
            critical_risk_transactions=fraud[
                "critical_risk_transactions"
            ],
            # Transaction value is not persisted yet.
            total_transaction_amount=Decimal("0"),
            fraudulent_transaction_amount=Decimal("0"),
            protected_amount=Decimal("0"),
            total_cases=total_cases,
            open_cases=cases["open_cases"],
            closed_cases=closed_cases,
            escalated_cases=escalated_cases,
            resolution_rate=self.repository.calculate_percentage(
                closed_cases,
                total_cases,
            ),
            escalation_rate=self.repository.calculate_percentage(
                escalated_cases,
                total_cases,
            ),
            period=self._period(start_at, end_at),
        )

    def get_risk_distribution(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> RiskDistributionResponse:
        """Build normalized fraud-risk distribution."""

        start_at, end_at = self.repository.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.repository.get_risk_distribution(
            start_at=start_at,
            end_at=end_at,
        )

        counts = {level: 0 for level in AnalyticsRiskLevel}
        average_scores = {level: 0.0 for level in AnalyticsRiskLevel}

        for row in rows:
            level = self._normalize_risk_level(row["risk_level"])
            counts[level] += row["transaction_count"]
            average_scores[level] = row["average_fraud_score"]

        total = sum(counts.values())

        items = [
            RiskDistributionItem(
                risk_level=level,
                transaction_count=counts[level],
                percentage=self.repository.calculate_percentage(
                    counts[level],
                    total,
                ),
                transaction_amount=Decimal("0"),
                average_fraud_score=round(
                    average_scores[level],
                    6,
                ),
            )
            for level in AnalyticsRiskLevel
        ]

        return RiskDistributionResponse(
            total_transactions=total,
            period=self._period(start_at, end_at),
            items=items,
        )

    def get_fraud_score_distribution(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        bucket_count: int = DEFAULT_HISTOGRAM_BUCKETS,
    ) -> FraudScoreDistributionResponse:
        """Build a histogram of persisted fraud probabilities."""

        if bucket_count < 2 or bucket_count > 50:
            raise AnalyticsValidationError(
                "Fraud-score bucket count must be between 2 and 50."
            )

        start_at, end_at = self.repository.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        scores = self.repository.get_fraud_score_values(
            start_at=start_at,
            end_at=end_at,
        )

        if not scores:
            return FraudScoreDistributionResponse(
                total_transactions=0,
                average_score=0.0,
                minimum_score=0.0,
                maximum_score=0.0,
                period=self._period(start_at, end_at),
                buckets=[],
            )

        width = 1.0 / bucket_count
        counts = [0 for _ in range(bucket_count)]

        for score in scores:
            normalized = min(max(float(score), 0.0), 1.0)

            index = min(
                int(normalized / width),
                bucket_count - 1,
            )
            counts[index] += 1

        total = len(scores)
        buckets: list[FraudScoreBucket] = []

        for index, count in enumerate(counts):
            minimum = round(index * width, 6)
            maximum = round((index + 1) * width, 6)

            if index == bucket_count - 1:
                maximum = 1.0

            buckets.append(
                FraudScoreBucket(
                    minimum_score=minimum,
                    maximum_score=maximum,
                    transaction_count=count,
                    percentage=self.repository.calculate_percentage(
                        count,
                        total,
                    ),
                )
            )

        return FraudScoreDistributionResponse(
            total_transactions=total,
            average_score=round(mean(scores), 6),
            minimum_score=round(min(scores), 6),
            maximum_score=round(max(scores), 6),
            period=self._period(start_at, end_at),
            buckets=buckets,
        )

    def get_fraud_trend(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        grouping: AnalyticsPeriod = AnalyticsPeriod.DAY,
    ) -> FraudTrendResponse:
        """
        Build a fraud trend.

        Bundle 2 supports daily grouping because `func.date()` works across
        both PostgreSQL and SQLite test databases.
        """

        if grouping != AnalyticsPeriod.DAY:
            raise AnalyticsValidationError(
                "Bundle 2 currently supports daily fraud-trend grouping only."
            )

        start_at, end_at = self.repository.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.repository.get_daily_fraud_trend(
            start_at=start_at,
            end_at=end_at,
        )

        points = []

        for row in rows:
            total = row["transaction_count"]
            fraudulent = row["fraudulent_count"]

            points.append(
                FraudTrendPoint(
                    period_start=self._to_datetime(
                        row["period_start"]
                    ),
                    transaction_count=total,
                    fraudulent_count=fraudulent,
                    legitimate_count=max(
                        total - fraudulent,
                        0,
                    ),
                    fraud_rate=self.repository.calculate_percentage(
                        fraudulent,
                        total,
                    ),
                    average_fraud_score=round(
                        row["average_fraud_score"],
                        6,
                    ),
                    transaction_amount=Decimal("0"),
                    fraudulent_amount=Decimal("0"),
                )
            )

        return FraudTrendResponse(
            grouping=grouping,
            period=self._period(start_at, end_at),
            points=points,
        )

    def get_case_status_distribution(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> CaseStatusDistributionResponse:
        """Build case workflow status distribution."""

        start_at, end_at = self.repository.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.repository.get_case_status_distribution(
            start_at=start_at,
            end_at=end_at,
        )

        total = sum(row["case_count"] for row in rows)

        return CaseStatusDistributionResponse(
            total_cases=total,
            period=self._period(start_at, end_at),
            items=[
                CaseStatusDistributionItem(
                    status=row["status"],
                    case_count=row["case_count"],
                    percentage=self.repository.calculate_percentage(
                        row["case_count"],
                        total,
                    ),
                )
                for row in rows
            ],
        )

    def get_investigator_performance(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> InvestigatorPerformanceResponse:
        """Build investigator workload and resolution metrics."""

        start_at, end_at = self.repository.validate_date_range(
            start_at=start_at,
            end_at=end_at,
        )

        rows = self.repository.get_investigator_performance(
            start_at=start_at,
            end_at=end_at,
        )

        items = []

        for row in rows:
            assigned = row["assigned_cases"]
            resolved = row["resolved_cases"]
            escalated = row["escalated_cases"]

            items.append(
                InvestigatorPerformanceItem(
                    investigator_id=row["investigator_id"],
                    investigator_name=row["investigator_name"],
                    assigned_cases=assigned,
                    open_cases=row["open_cases"],
                    resolved_cases=resolved,
                    escalated_cases=escalated,
                    resolution_rate=(
                        self.repository.calculate_percentage(
                            resolved,
                            assigned,
                        )
                    ),
                    escalation_rate=(
                        self.repository.calculate_percentage(
                            escalated,
                            assigned,
                        )
                    ),
                    average_resolution_hours=row[
                        "average_resolution_hours"
                    ],
                )
            )

        return InvestigatorPerformanceResponse(
            period=self._period(start_at, end_at),
            items=items,
        )

    def get_high_risk_transactions(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> HighRiskTransactionResponse:
        """Build paginated high-risk transaction summaries."""

        try:
            records, total = (
                self.repository.get_high_risk_transactions(
                    start_at=start_at,
                    end_at=end_at,
                    limit=limit,
                    offset=offset,
                )
            )
        except AnalyticsRepositoryError as exc:
            raise AnalyticsValidationError(str(exc)) from exc

        case_map = self.repository.get_case_by_score_record_ids(
            [record.id for record in records]
        )

        items = []

        for record in records:
            fraud_case = case_map.get(record.id)

            items.append(
                HighRiskTransactionItem(
                    transaction_id=str(record.transaction_id),
                    fraud_score=float(record.fraud_probability),
                    is_fraud=bool(record.fraud_prediction),
                    risk_level=self._normalize_risk_level(
                        record.risk_band
                    ),
                    transaction_amount=None,
                    transaction_date=record.created_at,
                    product_code=None,
                    case_id=(
                        fraud_case.id
                        if fraud_case is not None
                        else None
                    ),
                    case_status=(
                        fraud_case.case_status
                        if fraud_case is not None
                        else None
                    ),
                )
            )

        return HighRiskTransactionResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_health(self) -> AnalyticsHealthResponse:
        """Return analytics subsystem and source availability."""

        availability = self.repository.get_data_availability()

        return AnalyticsHealthResponse(
            status="healthy",
            generated_at=datetime.now(timezone.utc),
            **availability,
        )

    def get_dashboard_summary(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        high_risk_limit: int = 10,
    ) -> DashboardSummaryResponse:
        """Build the primary combined executive dashboard payload."""

        executive_kpis = self.get_executive_kpis(
            start_at=start_at,
            end_at=end_at,
        )

        risk_distribution = self.get_risk_distribution(
            start_at=start_at,
            end_at=end_at,
        )

        fraud_trend = self.get_fraud_trend(
            start_at=start_at,
            end_at=end_at,
            grouping=AnalyticsPeriod.DAY,
        )

        case_distribution = self.get_case_status_distribution(
            start_at=start_at,
            end_at=end_at,
        )

        high_risk = self.get_high_risk_transactions(
            start_at=start_at,
            end_at=end_at,
            limit=high_risk_limit,
            offset=0,
        )

        return DashboardSummaryResponse(
            executive_kpis=executive_kpis,
            risk_distribution=risk_distribution,
            fraud_trend=fraud_trend,
            case_distribution=case_distribution,
            high_risk_transactions=high_risk.items,
        )
