import os
from typing import Any

import pandas as pd

from backend.app.services.model_registry import (
    DEFAULT_MODEL_NAME,
    get_fraud_model,
    get_model_input_features,
    get_model_registry_health,
    resolve_model_path,
)

MODEL_NAME = DEFAULT_MODEL_NAME
MODEL_FILE = resolve_model_path()
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.84"))


def load_model():
    """
    Backward-compatible model loader.

    Existing imports can continue using load_model(), while the
    shared model registry remains the single source of truth.
    """
    return get_fraud_model()


def assign_risk_band(fraud_probability: float) -> str:
    if fraud_probability >= 0.84:
        return "high"

    if fraud_probability >= 0.50:
        return "medium"

    if fraud_probability >= 0.25:
        return "low"

    return "very_low"


def get_expected_feature_columns(model=None) -> list[str]:
    """
    Return the raw input columns expected by the model.

    The optional model parameter is retained for compatibility
    with existing tests and callers.
    """
    if model is not None and hasattr(model, "feature_names_in_"):
        return [
            str(feature)
            for feature in model.feature_names_in_
        ]

    return get_model_input_features()


def prepare_feature_frame(
    features: dict[str, Any],
    expected_columns: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    row = {
        column: features.get(column)
        for column in expected_columns
    }

    missing_features = [
        column
        for column in expected_columns
        if column not in features
    ]

    extra_features = [
        column
        for column in features
        if column not in expected_columns
    ]

    feature_quality = {
        "expected_feature_count": len(expected_columns),
        "missing_features_count": len(missing_features),
        "extra_features_count": len(extra_features),
        "missing_features_preview": missing_features[:10],
        "extra_features_preview": extra_features[:10],
    }

    return pd.DataFrame([row]), feature_quality


def score_transaction(
    features: dict[str, Any],
) -> dict[str, Any]:
    model = get_fraud_model()
    expected_columns = get_model_input_features()

    feature_frame, feature_quality = prepare_feature_frame(
        features=features,
        expected_columns=expected_columns,
    )

    fraud_probability = float(
        model.predict_proba(feature_frame)[0, 1]
    )

    fraud_prediction = int(
        fraud_probability >= FRAUD_THRESHOLD
    )

    return {
        "model_name": MODEL_NAME,
        "fraud_probability": fraud_probability,
        "fraud_prediction": fraud_prediction,
        "fraud_threshold": FRAUD_THRESHOLD,
        "risk_band": assign_risk_band(fraud_probability),
        "feature_quality": feature_quality,
    }


def get_model_health() -> dict[str, Any]:
    registry_health = get_model_registry_health()

    return {
        "status": registry_health["status"],
        "model_name": MODEL_NAME,
        "model_path": registry_health["model_path"],
        "fraud_threshold": FRAUD_THRESHOLD,
        "expected_feature_count": registry_health[
            "input_feature_count"
        ],
        "pipeline_type": registry_health["pipeline_type"],
        "classifier_type": registry_health["classifier_type"],
        "transformed_feature_count": registry_health[
            "transformed_feature_count"
        ],
    }
