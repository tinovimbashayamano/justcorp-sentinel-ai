from backend.app.services.explainability_service import (
    ExplainabilityService,
)


def test_health(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.explainability_service.get_explainability_health",
        lambda: {"status": "ready"},
    )

    service = ExplainabilityService()

    assert service.health()["status"] == "ready"


def test_explain(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.explainability_service.explain_transaction",
        lambda features, top_n: {
            "summary": "ok",
            "top_feature_count": top_n,
        },
    )

    service = ExplainabilityService()

    result = service.explain(
        {"TransactionAmt": 100},
        top_features=5,
    )

    assert result["summary"] == "ok"
    assert result["top_feature_count"] == 5


def test_score_and_explain(monkeypatch):
    monkeypatch.setattr(
        "backend.app.services.explainability_service.score_transaction",
        lambda features: {
            "fraud_probability": 0.91,
        },
    )

    monkeypatch.setattr(
        "backend.app.services.explainability_service.explain_transaction",
        lambda features, top_n: {
            "summary": "High amount",
        },
    )

    service = ExplainabilityService()

    result = service.score_and_explain(
        {"TransactionAmt": 100},
    )

    assert "prediction" in result
    assert "explanation" in result

    assert result["prediction"]["fraud_probability"] == 0.91
    assert result["explanation"]["summary"] == "High amount"
