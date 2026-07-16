from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import create_access_token, hash_password
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.user import User, UserRole
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


def create_authenticated_user_headers() -> dict[str, str]:
    db = TestingSessionLocal()

    try:
        user = User(
            username="fraudapitest",
            email="fraudapitest@example.com",
            full_name="Fraud API Test User",
            hashed_password=hash_password(
                "SecurePassword123!"
            ),
            role=UserRole.VIEWER,
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
    headers = create_authenticated_user_headers()

    response = client.get(
        "/api/v1/fraud/health",
        headers=headers,
    )

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

    headers = create_authenticated_user_headers()

    response = client.post(
        "/api/v1/fraud/score",
        json=payload,
        headers=headers,
    )

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
    headers = create_authenticated_user_headers()

    response = client.get(
        "/api/v1/fraud/score",
        headers=headers,
    )

    assert response.status_code == 405
