from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.user import User, UserRole


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def create_user_headers(
    username: str,
    role: UserRole,
) -> dict[str, str]:
    db = TestingSessionLocal()

    try:
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=f"{username} user",
            hashed_password=hash_password(
                "SecurePassword123!"
            ),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )

        return {
            "Authorization": f"Bearer {token}",
        }
    finally:
        db.close()


def feature_quality() -> dict:
    return {
        "expected_feature_count": 81,
        "missing_features_count": 80,
        "extra_features_count": 0,
        "missing_features_preview": ["ProductCD"],
        "extra_features_preview": [],
    }


def explanation_payload() -> dict:
    return {
        "model_name": "lightgbm_fraud_model",
        "explanation_type": "local",
        "fraud_probability": 0.91,
        "fraud_prediction": 1,
        "fraud_threshold": 0.84,
        "risk_band": "high",
        "base_value": -2.0,
        "top_feature_count": 1,
        "feature_contributions": [
            {
                "rank": 1,
                "transformed_feature": (
                    "numeric__TransactionAmt"
                ),
                "source_feature": "TransactionAmt",
                "category": None,
                "display_name": "TransactionAmt",
                "feature_value": 100.0,
                "shap_value": 0.7,
                "absolute_shap_value": 0.7,
                "impact_direction": (
                    "increases_fraud_risk"
                ),
                "impact_strength": "strong",
            }
        ],
        "feature_quality": feature_quality(),
        "summary": (
            "The model assigned a fraud probability of 91.00%."
        ),
    }


def prediction_payload() -> dict:
    return {
        "model_name": "lightgbm_fraud_model",
        "fraud_probability": 0.91,
        "fraud_prediction": 1,
        "fraud_threshold": 0.84,
        "risk_band": "high",
        "feature_quality": feature_quality(),
    }


def test_explainability_health_returns_200(monkeypatch):
    monkeypatch.setattr(
        "backend.app.api.fraud.explainability_service.health",
        lambda: {
            "status": "ready",
            "model_name": "lightgbm_fraud_model",
            "pipeline_type": "Pipeline",
            "classifier_type": "LGBMClassifier",
            "explainer_type": "TreeExplainer",
            "raw_feature_count": 81,
            "transformed_feature_count": 191,
        },
    )
    headers = create_user_headers(
        "explainhealth",
        UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/fraud/explainability/health",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["raw_feature_count"] == 81


def test_explain_returns_explanation_payload(monkeypatch):
    monkeypatch.setattr(
        "backend.app.api.fraud.explainability_service.explain",
        lambda features, top_features: explanation_payload(),
    )
    headers = create_user_headers(
        "explainanalyst",
        UserRole.FRAUD_ANALYST,
    )

    response = client.post(
        "/api/v1/fraud/explain",
        headers=headers,
        json={
            "transaction_id": "TX-EXPLAIN-1",
            "features": {"TransactionAmt": 100.0},
            "top_features": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fraud_probability"] == 0.91
    assert data["fraud_prediction"] == 1
    assert data["top_feature_count"] == 1
    assert (
        data["feature_contributions"][0]["source_feature"]
        == "TransactionAmt"
    )


def test_score_and_explain_returns_both_payloads_and_audits(
    monkeypatch,
):
    monkeypatch.setattr(
        (
            "backend.app.api.fraud.explainability_service."
            "score_and_explain"
        ),
        lambda features, top_features: {
            "prediction": prediction_payload(),
            "explanation": explanation_payload(),
        },
    )
    audit_log = Mock()
    monkeypatch.setattr(
        "backend.app.api.fraud.safely_create_audit_log",
        audit_log,
    )
    headers = create_user_headers(
        "scoreexplain",
        UserRole.ADMIN,
    )

    response = client.post(
        "/api/v1/fraud/score-and-explain",
        headers=headers,
        json={
            "transaction_id": "TX-SCORE-EXPLAIN-1",
            "features": {"TransactionAmt": 100.0},
            "top_features": 7,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TX-SCORE-EXPLAIN-1"
    assert data["prediction"]["fraud_probability"] == 0.91
    assert data["explanation"]["summary"].startswith(
        "The model assigned"
    )

    audit_log.assert_called_once()
    audit_arguments = audit_log.call_args.kwargs
    assert audit_arguments["action"] == AuditAction.FRAUD_SCORE
    assert audit_arguments["status"] == AuditStatus.SUCCESS
    assert audit_arguments["resource_type"] == "transaction"
    assert (
        audit_arguments["resource_id"]
        == "TX-SCORE-EXPLAIN-1"
    )
    assert (
        audit_arguments["details"]["explanation_requested"]
        is True
    )
    assert (
        audit_arguments["details"]["requested_top_features"]
        == 7
    )


def test_explainability_requires_authentication():
    response = client.get(
        "/api/v1/fraud/explainability/health"
    )

    assert response.status_code == 401


def test_viewer_cannot_explain_transaction():
    headers = create_user_headers(
        "explainviewer",
        UserRole.VIEWER,
    )

    response = client.post(
        "/api/v1/fraud/explain",
        headers=headers,
        json={
            "transaction_id": "TX-FORBIDDEN",
            "features": {},
        },
    )

    assert response.status_code == 403


def test_service_failure_returns_503(monkeypatch):
    def fail_explanation(features, top_features):
        raise RuntimeError("SHAP explainer is unavailable.")

    monkeypatch.setattr(
        "backend.app.api.fraud.explainability_service.explain",
        fail_explanation,
    )
    headers = create_user_headers(
        "explainfailure",
        UserRole.FRAUD_ANALYST,
    )

    response = client.post(
        "/api/v1/fraud/explain",
        headers=headers,
        json={
            "transaction_id": "TX-FAILURE",
            "features": {},
        },
    )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "SHAP explainer is unavailable."
    )


def test_invalid_service_request_returns_400(monkeypatch):
    def reject_features(features, top_features):
        raise ValueError("Transaction features are invalid.")

    monkeypatch.setattr(
        "backend.app.api.fraud.explainability_service.explain",
        reject_features,
    )
    headers = create_user_headers(
        "explaininvalid",
        UserRole.FRAUD_ANALYST,
    )

    response = client.post(
        "/api/v1/fraud/explain",
        headers=headers,
        json={
            "transaction_id": "TX-INVALID",
            "features": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Unable to explain transaction: "
        "Transaction features are invalid."
    )
