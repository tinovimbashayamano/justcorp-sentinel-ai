import base64

import pytest

from backend.app.services.explainability_visualization_service import (
    ExplainabilityVisualizationService,
)


class LocalExplainabilityStub:
    def health(self):
        return {"status": "ready"}

    def explain(self, features, top_features=10):
        return {
            "prediction": 1,
            "fraud_probability": 0.91,
            "risk_band": "high",
            "base_value": -1.2,
            "summary": "High risk.",
            "contributions": [
                {
                    "feature": "TransactionAmt",
                    "feature_value": 950,
                    "shap_value": 1.4,
                },
                {
                    "feature": "card1",
                    "feature_value": 1234,
                    "shap_value": -0.2,
                },
            ],
        }


class GlobalExplainabilityStub:
    def health(self):
        return {"status": "ready"}

    def compute_global_importance(self):
        return {
            "samples": 100,
            "generated_at": "2026-07-27T08:00:00+00:00",
            "features": [
                {
                    "rank": 1,
                    "feature": "TransactionAmt",
                    "importance": 0.8,
                },
                {
                    "rank": 2,
                    "feature": "card1",
                    "importance": 0.5,
                },
            ],
        }

    def get_dependence_data(
        self,
        feature_name,
        limit=500,
    ):
        if feature_name != "TransactionAmt":
            raise KeyError(feature_name)
        return {
            "feature": feature_name,
            "points": [
                {
                    "feature_value": 100,
                    "shap_value": 0.1,
                },
                {
                    "feature_value": 900,
                    "shap_value": 1.2,
                },
            ],
            "sample_count": 2,
        }


@pytest.fixture
def service():
    return ExplainabilityVisualizationService(
        LocalExplainabilityStub(),
        GlobalExplainabilityStub(),
    )


def test_health(service):
    assert service.health()["status"] == "ready"


def test_local_data(service):
    result = service.local_visualization_data(
        "TX1",
        {},
        2,
    )

    assert result["points"][0]["feature"] == "TransactionAmt"


def test_waterfall(service):
    result = service.waterfall_plot("TX1", {}, 2)

    assert base64.b64decode(
        result["image_base64"]
    ).startswith(b"\x89PNG")


def test_force(service):
    result = service.force_plot("TX1", {}, 2)

    assert base64.b64decode(
        result["image_base64"]
    ).startswith(b"\x89PNG")


def test_global(service):
    result = service.global_visualization_data(1)

    assert result["features"][0]["feature"] == "TransactionAmt"


def test_summary_png(service):
    result = service.global_summary_plot(2)

    assert base64.b64decode(
        result["image_base64"]
    ).startswith(b"\x89PNG")


def test_dependence(service):
    result = service.dependence_data("TransactionAmt")

    assert result["sample_count"] == 2


def test_html_export(service):
    result = service.export_report(
        "html",
        transaction_id="TX1",
        features={},
    )

    assert (
        b"Fraud Investigation Explainability Report"
        in base64.b64decode(result["content_base64"])
    )


def test_pdf_export(service):
    result = service.export_report(
        "pdf",
        transaction_id="TX1",
        features={},
    )

    assert base64.b64decode(
        result["content_base64"]
    ).startswith(b"%PDF")


def test_bad_format(service):
    with pytest.raises(ValueError):
        service.export_report(
            "docx",
            transaction_id="TX1",
            features={},
        )
