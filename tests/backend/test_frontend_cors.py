from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app


client = TestClient(app)


def test_frontend_origin_can_complete_cors_preflight():
    response = client.options(
        "/api/v1/fraud/cases",
        headers={
            "Origin": settings.frontend_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": (
                "authorization"
            ),
        },
    )

    assert response.status_code == 200
    assert response.headers[
        "access-control-allow-origin"
    ] == settings.frontend_origin
