import os
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names.*",
    category=UserWarning,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_MODEL_PATH = "ml/model_artifacts/lightgbm_fraud_model.joblib"
MODEL_NAME = "lightgbm_fraud_model"
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.84"))


def resolve_model_path() -> Path:
    configured_path = os.getenv("FRAUD_MODEL_PATH", DEFAULT_MODEL_PATH)
    model_path = Path(configured_path)

    if model_path.is_absolute():
        return model_path

    return PROJECT_ROOT / model_path


MODEL_FILE = resolve_model_path()


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_FILE.exists():
        raise RuntimeError(
            f"Fraud model artifact not found: {MODEL_FILE}. "
            "Run ml/src/models/train_lightgbm_model.py first."
        )

    return joblib.load(MODEL_FILE)


def assign_risk_band(fraud_probability: float) -> str:
    if fraud_probability >= 0.84:
        return "high"
    if fraud_probability >= 0.50:
        return "medium"
    if fraud_probability >= 0.25:
        return "low"
    return "very_low"


def get_expected_feature_columns(model) -> list[str]:
    preprocessor = model.named_steps["preprocessor"]

    expected_columns: list[str] = []

    for _, transformer, columns in preprocessor.transformers_:
        if transformer == "drop":
            continue

        if isinstance(columns, list):
            expected_columns.extend(columns)
        else:
            expected_columns.extend(list(columns))

    return expected_columns


def prepare_feature_frame(
    features: dict[str, Any],
    expected_columns: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    row = {}

    for column in expected_columns:
        row[column] = features.get(column, None)

    missing_features = [column for column in expected_columns if column not in features]
    extra_features = [column for column in features.keys() if column not in expected_columns]

    feature_quality = {
        "expected_feature_count": len(expected_columns),
        "missing_features_count": len(missing_features),
        "extra_features_count": len(extra_features),
        "missing_features_preview": missing_features[:10],
        "extra_features_preview": extra_features[:10],
    }

    return pd.DataFrame([row]), feature_quality


def score_transaction(features: dict[str, Any]) -> dict[str, Any]:
    model = load_model()
    expected_columns = get_expected_feature_columns(model)

    feature_frame, feature_quality = prepare_feature_frame(
        features=features,
        expected_columns=expected_columns,
    )

    fraud_probability = float(model.predict_proba(feature_frame)[0, 1])
    fraud_prediction = int(fraud_probability >= FRAUD_THRESHOLD)

    return {
        "model_name": MODEL_NAME,
        "fraud_probability": fraud_probability,
        "fraud_prediction": fraud_prediction,
        "fraud_threshold": FRAUD_THRESHOLD,
        "risk_band": assign_risk_band(fraud_probability),
        "feature_quality": feature_quality,
    }


def get_model_health() -> dict[str, Any]:
    model = load_model()
    expected_columns = get_expected_feature_columns(model)

    return {
        "status": "ready",
        "model_name": MODEL_NAME,
        "model_path": str(MODEL_FILE),
        "fraud_threshold": FRAUD_THRESHOLD,
        "expected_feature_count": len(expected_columns),
    }
