"""API tests for model insight endpoints, validation, and RBAC."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app.api.model_insights import (
    get_model_insight_service,
)
from backend.app.core.dependencies import get_current_active_user
from backend.app.main import app
from backend.app.models.user import User, UserRole
from backend.app.schemas.model_insights import (
    FeatureDetailResponse,
    FeatureImportance,
    GlobalImportanceResponse,
    InsightHealthResponse,
    TopFeaturesResponse,
)
from backend.app.services.model_insight_service import (
    ModelInsightNotFoundError,
)


client = TestClient(app)
GENERATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


class StubModelInsightService:
    def __init__(self) -> None:
        self.refresh_count = 0

    def health(self):
        return InsightHealthResponse(
            status="ready",
            model="LightGBM",
            samples_used=5_000,
            feature_count=191,
        )

    def compute_global_importance(self):
        return self.get_feature_rankings(limit=2)

    def get_feature_rankings(
        self,
        *,
        limit=20,
        sort="importance",
    ):
        features = [
            FeatureImportance(
                rank=1,
                feature="TransactionAmt",
                importance=0.1832,
            ),
            FeatureImportance(
                rank=2,
                feature="card1",
                importance=0.1428,
            ),
        ]

        if sort == "feature":
            features.sort(key=lambda item: item.feature)

        return GlobalImportanceResponse(
            generated_at=GENERATED_AT,
            samples=5_000,
            features=features[:limit],
        )

    def get_feature(self, feature_name):
        if feature_name != "TransactionAmt":
            raise ModelInsightNotFoundError(
                f"Unknown transformed model feature: {feature_name}."
            )

        return FeatureDetailResponse(
            feature=feature_name,
            rank=1,
            mean_abs_shap=0.1832,
            positive_effect=63.2,
            negative_effect=36.8,
            minimum=0.0,
            maximum=25_000.0,
            mean=163.8,
            median=42.1,
        )

    def top_positive(self, *, limit=20):
        return TopFeaturesResponse(
            generated_at=GENERATED_AT,
            direction="positive",
            features=[
                FeatureImportance(
                    rank=1,
                    feature="TransactionAmt",
                    importance=0.12,
                )
            ][:limit],
        )

    def top_negative(self, *, limit=20):
        return TopFeaturesResponse(
            generated_at=GENERATED_AT,
            direction="negative",
            features=[
                FeatureImportance(
                    rank=1,
                    feature="card1",
                    importance=0.08,
                )
            ][:limit],
        )

    def refresh_cache(self):
        self.refresh_count += 1
        return self.compute_global_importance()


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def stub_service():
    service = StubModelInsightService()
    app.dependency_overrides[
        get_model_insight_service
    ] = lambda: service
    return service


def user_for_role(role: UserRole) -> User:
    return User(
        id=1,
        username=f"insight-{role.value}",
        email=f"insight-{role.value}@example.com",
        hashed_password="not-used",
        role=role,
        is_active=True,
    )


def authenticate_as(role: UserRole) -> None:
    user = user_for_role(role)
    app.dependency_overrides[
        get_current_active_user
    ] = lambda: user


def test_model_insight_authentication_is_required(stub_service):
    response = client.get("/api/v1/model-insights/health")

    assert response.status_code == 401


def test_health_is_available_to_any_authenticated_user(stub_service):
    authenticate_as(UserRole.VIEWER)

    response = client.get("/api/v1/model-insights/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "model": "LightGBM",
        "samples_used": 5_000,
        "feature_count": 191,
    }


@pytest.mark.parametrize(
    "role",
    [
        UserRole.ADMIN,
        UserRole.FRAUD_ANALYST,
        UserRole.AUDITOR,
    ],
)
def test_authorized_roles_can_get_global_insights(
    stub_service,
    role,
):
    authenticate_as(role)

    response = client.get("/api/v1/model-insights/global")

    assert response.status_code == 200
    assert response.json()["features"][0]["rank"] == 1


def test_viewer_cannot_access_protected_insights(stub_service):
    authenticate_as(UserRole.VIEWER)

    response = client.get("/api/v1/model-insights/global")

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("path", "expected_key"),
    [
        ("/api/v1/model-insights/global", "samples"),
        (
            "/api/v1/model-insights/features?limit=1&sort=importance",
            "features",
        ),
        (
            "/api/v1/model-insights/features/TransactionAmt",
            "mean_abs_shap",
        ),
        ("/api/v1/model-insights/top-positive", "direction"),
        ("/api/v1/model-insights/top-negative", "direction"),
    ],
)
def test_model_insight_endpoints_return_200(
    stub_service,
    path,
    expected_key,
):
    authenticate_as(UserRole.FRAUD_ANALYST)

    response = client.get(path)

    assert response.status_code == 200
    assert expected_key in response.json()


def test_invalid_feature_returns_404(stub_service):
    authenticate_as(UserRole.AUDITOR)

    response = client.get(
        "/api/v1/model-insights/features/unknown"
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "query",
    ["limit=0", "sort=unsupported"],
)
def test_invalid_feature_query_returns_422(
    stub_service,
    query,
):
    authenticate_as(UserRole.ADMIN)

    response = client.get(
        f"/api/v1/model-insights/features?{query}"
    )

    assert response.status_code == 422


def test_refresh_cache_endpoint(stub_service):
    authenticate_as(UserRole.ADMIN)

    response = client.post(
        "/api/v1/model-insights/refresh-cache"
    )

    assert response.status_code == 200
    assert stub_service.refresh_count == 1
