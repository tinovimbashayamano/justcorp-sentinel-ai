"""Integration tests for the fraud analytics API."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import create_access_token
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User, UserRole


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
client = TestClient(app)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def create_user(
    username: str,
    role: UserRole,
    *,
    is_active: bool = True,
) -> User:
    with TestingSessionLocal() as db:
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password="not-used-by-token-tests",
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


def seed_analytics_data(analyst: User) -> None:
    with TestingSessionLocal() as db:
        scores = [
            FraudScoreRecord(
                transaction_id="TX-LOW",
                model_name="test-model",
                fraud_probability=0.10,
                fraud_prediction=0,
                fraud_threshold=0.50,
                risk_band="low",
                feature_quality={},
            ),
            FraudScoreRecord(
                transaction_id="TX-MEDIUM",
                model_name="test-model",
                fraud_probability=0.45,
                fraud_prediction=0,
                fraud_threshold=0.50,
                risk_band="medium",
                feature_quality={},
            ),
            FraudScoreRecord(
                transaction_id="TX-HIGH",
                model_name="test-model",
                fraud_probability=0.78,
                fraud_prediction=1,
                fraud_threshold=0.50,
                risk_band="high",
                feature_quality={},
            ),
            FraudScoreRecord(
                transaction_id="TX-CRITICAL",
                model_name="test-model",
                fraud_probability=0.96,
                fraud_prediction=1,
                fraud_threshold=0.50,
                risk_band="critical",
                feature_quality={},
            ),
        ]
        db.add_all(scores)
        db.flush()

        db.add_all(
            [
                FraudCaseReview(
                    fraud_score_record_id=scores[2].id,
                    case_status="open",
                    priority="high",
                    assigned_to_user_id=analyst.id,
                ),
                FraudCaseReview(
                    fraud_score_record_id=scores[3].id,
                    case_status="closed",
                    priority="critical",
                    assigned_to_user_id=analyst.id,
                ),
            ]
        )
        db.commit()


def test_analytics_authentication_is_required():
    response = client.get("/api/v1/analytics/health")

    assert response.status_code == 401


@pytest.mark.parametrize(
    "role",
    [
        UserRole.ADMIN,
        UserRole.FRAUD_ANALYST,
        UserRole.AUDITOR,
    ],
)
def test_authorized_roles_can_access_analytics(role: UserRole):
    user = create_user(f"analytics-{role.value}", role)

    response = client.get(
        "/api/v1/analytics/health",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_dashboard_response_combines_analytics_sections():
    analyst = create_user("dashboard-analyst", UserRole.FRAUD_ANALYST)
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/dashboard?high_risk_limit=1",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["executive_kpis"]["total_transactions"] == 4
    assert body["risk_distribution"]["total_transactions"] == 4
    assert len(body["fraud_trend"]["points"]) == 1
    assert body["case_distribution"]["total_cases"] == 2
    assert len(body["high_risk_transactions"]) == 1


def test_executive_kpis_return_supported_metrics():
    analyst = create_user("kpi-analyst", UserRole.FRAUD_ANALYST)
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/executive-kpis",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 4
    assert body["fraudulent_transactions"] == 2
    assert body["legitimate_transactions"] == 2
    assert body["fraud_rate"] == 50.0
    assert body["total_cases"] == 2
    assert Decimal(str(body["total_transaction_amount"])) == Decimal("0")
    assert (
        Decimal(str(body["fraudulent_transaction_amount"]))
        == Decimal("0")
    )
    assert Decimal(str(body["protected_amount"])) == Decimal("0")


def test_risk_distribution_returns_all_risk_bands():
    analyst = create_user("risk-analyst", UserRole.FRAUD_ANALYST)
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/risk-distribution",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 4
    assert {
        item["risk_level"] for item in body["items"]
    } == {
        "low",
        "medium",
        "high",
        "critical",
    }
    assert all(
        Decimal(str(item["transaction_amount"])) == Decimal("0")
        for item in body["items"]
    )


def test_fraud_score_distribution_returns_requested_buckets():
    analyst = create_user("score-analyst", UserRole.FRAUD_ANALYST)
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/fraud-score-distribution?bucket_count=4",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 4
    assert len(body["buckets"]) == 4
    assert sum(
        bucket["transaction_count"] for bucket in body["buckets"]
    ) == 4


def test_daily_fraud_trend_returns_daily_points():
    analyst = create_user("trend-analyst", UserRole.FRAUD_ANALYST)
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/fraud-trend?grouping=day",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grouping"] == "day"
    assert len(body["points"]) == 1
    assert body["points"][0]["transaction_count"] == 4
    assert body["points"][0]["fraudulent_count"] == 2


def test_case_status_distribution_returns_case_counts():
    analyst = create_user("case-analytics", UserRole.FRAUD_ANALYST)
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/case-status-distribution",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_cases"] == 2
    assert {
        item["status"]: item["case_count"] for item in body["items"]
    } == {
        "closed": 1,
        "open": 1,
    }


def test_investigator_performance_returns_workload():
    analyst = create_user(
        "performance-analyst",
        UserRole.FRAUD_ANALYST,
    )
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/investigator-performance",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["investigator_id"] == analyst.id
    assert item["assigned_cases"] == 2
    assert item["open_cases"] == 1
    assert item["resolved_cases"] == 1
    assert item["average_resolution_hours"] is None


def test_high_risk_transactions_support_pagination():
    analyst = create_user("pagination-analyst", UserRole.FRAUD_ANALYST)
    seed_analytics_data(analyst)

    response = client.get(
        "/api/v1/analytics/high-risk-transactions?limit=1&offset=1",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["items"]) == 1
    assert isinstance(body["items"][0]["transaction_id"], str)
    assert body["items"][0]["transaction_amount"] is None
    assert body["items"][0]["product_code"] is None


def test_invalid_date_range_returns_422():
    analyst = create_user("date-range-analyst", UserRole.FRAUD_ANALYST)

    response = client.get(
        "/api/v1/analytics/executive-kpis"
        "?start_at=2026-02-01T00:00:00Z"
        "&end_at=2026-01-01T00:00:00Z",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 422


def test_unsupported_grouping_returns_422():
    analyst = create_user("grouping-analyst", UserRole.FRAUD_ANALYST)

    response = client.get(
        "/api/v1/analytics/fraud-trend?grouping=month",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 422


@pytest.mark.parametrize("bucket_count", [1, 51])
def test_invalid_bucket_count_returns_422(bucket_count: int):
    analyst = create_user(
        f"bucket-analyst-{bucket_count}",
        UserRole.FRAUD_ANALYST,
    )

    response = client.get(
        "/api/v1/analytics/fraud-score-distribution"
        f"?bucket_count={bucket_count}",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "query",
    [
        "limit=0&offset=0",
        "limit=101&offset=0",
        "limit=20&offset=-1",
    ],
)
def test_invalid_high_risk_pagination_returns_422(query: str):
    analyst = create_user(
        f"invalid-pagination-{abs(hash(query))}",
        UserRole.FRAUD_ANALYST,
    )

    response = client.get(
        f"/api/v1/analytics/high-risk-transactions?{query}",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 422
