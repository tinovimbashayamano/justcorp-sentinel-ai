from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.services.fraud_scoring_service import MODEL_FILE


MODEL_AVAILABLE = Path(MODEL_FILE).exists()


SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
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


@pytest.mark.skipif(
    not MODEL_AVAILABLE,
    reason="LightGBM model artifact is not available locally.",
)
def test_score_and_save_fraud_transaction():
    payload = {
        "transaction_id": "storage-test-001",
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

    response = client.post("/api/v1/fraud/score/save", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["transaction_id"] == "storage-test-001"
    assert data["model_name"] == "lightgbm_fraud_model"
    assert 0 <= data["fraud_probability"] <= 1
    assert data["fraud_prediction"] in [0, 1]
    assert data["fraud_threshold"] == 0.84
    assert data["risk_band"] in ["very_low", "low", "medium", "high"]
    assert data["feature_quality"]["expected_feature_count"] == 81


@pytest.mark.skipif(
    not MODEL_AVAILABLE,
    reason="LightGBM model artifact is not available locally.",
)
def test_recent_fraud_scores_endpoint_returns_saved_records():
    payload = {
        "transaction_id": "storage-test-002",
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

    save_response = client.post("/api/v1/fraud/score/save", json=payload)

    assert save_response.status_code == 200

    list_response = client.get("/api/v1/fraud/scores?limit=5")

    assert list_response.status_code == 200

    data = list_response.json()

    assert len(data) == 1
    assert data[0]["transaction_id"] == "storage-test-002"
    assert data[0]["model_name"] == "lightgbm_fraud_model"


def test_recent_fraud_scores_limit_validation():
    response = client.get("/api/v1/fraud/scores?limit=0")

    assert response.status_code == 422
