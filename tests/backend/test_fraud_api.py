from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.fraud_scoring_service import MODEL_FILE


client = TestClient(app)


MODEL_AVAILABLE = Path(MODEL_FILE).exists()


def test_root_endpoint_returns_ok():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "JustCorp Sentinel AI" in data["message"]


@pytest.mark.skipif(
    not MODEL_AVAILABLE,
    reason="LightGBM model artifact is not available locally.",
)
def test_fraud_model_health_endpoint():
    response = client.get("/api/v1/fraud/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert data["model_name"] == "lightgbm_fraud_model"
    assert data["fraud_threshold"] == 0.84
    assert data["expected_feature_count"] == 81


@pytest.mark.skipif(
    not MODEL_AVAILABLE,
    reason="LightGBM model artifact is not available locally.",
)
def test_fraud_score_endpoint_returns_prediction():
    payload = {
        "transaction_id": "test-001",
        "features": {
            "TransactionAmt": 120.5,
            "ProductCD": "W",
            "card1": 12345,
            "card2": 150,
            "card3": 150,
            "card4": "visa",
            "card5": 226,
            "card6": "credit",
            "addr1": 315,
            "addr2": 87,
            "C1": 1,
            "C2": 1,
            "C4": 0,
            "TransactionAmt_log": 4.8,
            "transaction_hour": 12,
            "transaction_day": 1,
            "has_identity": 0,
        },
    }

    response = client.post("/api/v1/fraud/score", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["transaction_id"] == "test-001"
    assert data["model_name"] == "lightgbm_fraud_model"
    assert 0 <= data["fraud_probability"] <= 1
    assert data["fraud_prediction"] in [0, 1]
    assert data["fraud_threshold"] == 0.84
    assert data["risk_band"] in ["very_low", "low", "medium", "high"]

    feature_quality = data["feature_quality"]

    assert feature_quality["expected_feature_count"] == 81
    assert feature_quality["extra_features_count"] == 0


def test_fraud_score_endpoint_does_not_accept_get():
    response = client.get("/api/v1/fraud/score")

    assert response.status_code == 405
