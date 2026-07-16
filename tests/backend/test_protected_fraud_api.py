from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_fraud_model_health_requires_authentication():
    response = client.get("/api/v1/fraud/health")

    assert response.status_code == 401


def test_fraud_score_requires_authentication():
    response = client.post(
        "/api/v1/fraud/score",
        json={
            "transaction_id": "unauthorized-test",
            "features": {},
        },
    )

    assert response.status_code == 401


def test_score_and_save_requires_authentication():
    response = client.post(
        "/api/v1/fraud/score/save",
        json={
            "transaction_id": "unauthorized-save-test",
            "features": {},
        },
    )

    assert response.status_code == 401


def test_fraud_scores_require_authentication():
    response = client.get("/api/v1/fraud/scores")

    assert response.status_code == 401


def test_fraud_cases_require_authentication():
    response = client.get("/api/v1/fraud/cases")

    assert response.status_code == 401


def test_invalid_token_is_rejected():
    response = client.get(
        "/api/v1/fraud/scores",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
