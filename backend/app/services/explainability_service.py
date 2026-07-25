from typing import Any

from backend.app.explainability.shap_engine import (
    explain_transaction,
    get_explainability_health,
)
from backend.app.services.fraud_scoring_service import (
    score_transaction,
)


class ExplainabilityService:
    """
    Application service for fraud explainability.

    Responsibilities
    ----------------
    • Coordinate fraud scoring and SHAP explanations.
    • Expose a stable interface to the API layer.
    • Avoid exposing SHAP internals to controllers.
    """

    def score_and_explain(
        self,
        features: dict[str, Any],
        *,
        top_features: int = 10,
    ) -> dict[str, Any]:
        """
        Produce both the fraud prediction and the local explanation.
        """

        prediction = score_transaction(features)

        explanation = explain_transaction(
            features,
            top_n=top_features,
        )

        return {
            "prediction": prediction,
            "explanation": explanation,
        }

    def explain(
        self,
        features: dict[str, Any],
        *,
        top_features: int = 10,
    ) -> dict[str, Any]:
        """
        Produce only a local explanation.
        """

        return explain_transaction(
            features,
            top_n=top_features,
        )

    def health(self) -> dict[str, Any]:
        """
        Explainability subsystem health.
        """

        return get_explainability_health()


explainability_service = ExplainabilityService()
