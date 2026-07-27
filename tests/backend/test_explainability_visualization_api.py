from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_requires_auth():
    response = client.get(
        "/api/v1/explainability-visualizations/health"
    )

    assert response.status_code in {401, 403}


def test_invalid_top_features():
    response = client.post(
        "/api/v1/explainability-visualizations/local/data",
        json={
            "transaction_id": "TX1",
            "features": {},
            "top_features": 0,
        },
    )

    assert response.status_code in {401, 403, 422}


def test_invalid_limit():
    response = client.get(
        "/api/v1/explainability-visualizations/global/data"
        "?limit=0"
    )

    assert response.status_code in {401, 403, 422}


def test_report_export_route_is_registered():
    operation = app.openapi()["paths"][
        (
            "/api/v1/explainability-visualizations/"
            "reports/{report_format}"
        )
    ]["post"]

    assert "Explainability Visualizations" in operation["tags"]
    assert "requestBody" in operation
