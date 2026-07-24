import os
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names.*",
    category=UserWarning,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_MODEL_PATH = "ml/model_artifacts/lightgbm_fraud_model.joblib"
DEFAULT_MODEL_NAME = "lightgbm_fraud_model"


class ModelRegistryError(RuntimeError):
    """Raised when a registered model cannot be loaded or validated."""


def resolve_model_path(
    configured_path: str | None = None,
) -> Path:
    raw_path = configured_path or os.getenv(
        "FRAUD_MODEL_PATH",
        DEFAULT_MODEL_PATH,
    )

    model_path = Path(raw_path)

    if model_path.is_absolute():
        return model_path

    return PROJECT_ROOT / model_path


def validate_model_pipeline(model: Any) -> None:
    if not hasattr(model, "named_steps"):
        raise ModelRegistryError(
            "Fraud model must be an sklearn-compatible pipeline "
            "with named_steps."
        )

    required_steps = {"preprocessor", "classifier"}
    available_steps = set(model.named_steps.keys())
    missing_steps = required_steps - available_steps

    if missing_steps:
        missing = ", ".join(sorted(missing_steps))
        raise ModelRegistryError(
            f"Fraud model pipeline is missing required steps: {missing}."
        )

    if not hasattr(model, "predict_proba"):
        raise ModelRegistryError(
            "Fraud model must expose predict_proba()."
        )


@lru_cache(maxsize=1)
def get_fraud_model():
    model_path = resolve_model_path()

    if not model_path.exists():
        raise ModelRegistryError(
            f"Fraud model artifact not found: {model_path}. "
            "Run ml/src/models/train_lightgbm_model.py first."
        )

    try:
        model = joblib.load(model_path)
    except Exception as exc:
        raise ModelRegistryError(
            f"Unable to load fraud model artifact: {model_path}."
        ) from exc

    validate_model_pipeline(model)

    return model


def get_fraud_preprocessor():
    return get_fraud_model().named_steps["preprocessor"]


def get_fraud_classifier():
    return get_fraud_model().named_steps["classifier"]


def get_model_input_features() -> list[str]:
    model = get_fraud_model()

    if hasattr(model, "feature_names_in_"):
        return [str(feature) for feature in model.feature_names_in_]

    preprocessor = get_fraud_preprocessor()
    expected_columns: list[str] = []

    for _, transformer, columns in preprocessor.transformers_:
        if transformer == "drop":
            continue

        if isinstance(columns, str):
            expected_columns.append(columns)
        else:
            expected_columns.extend(str(column) for column in columns)

    return expected_columns


def get_transformed_feature_names() -> list[str]:
    preprocessor = get_fraud_preprocessor()

    try:
        return [
            str(feature)
            for feature in preprocessor.get_feature_names_out()
        ]
    except Exception:
        classifier = get_fraud_classifier()

        feature_importances = getattr(
            classifier,
            "feature_importances_",
            None,
        )

        if feature_importances is None:
            raise ModelRegistryError(
                "Unable to determine transformed feature names."
            )

        return [
            f"feature_{index}"
            for index in range(len(feature_importances))
        ]


def clear_model_registry_cache() -> None:
    get_fraud_model.cache_clear()


def get_model_registry_health() -> dict[str, Any]:
    model = get_fraud_model()
    classifier = get_fraud_classifier()
    model_path = resolve_model_path()

    return {
        "status": "ready",
        "model_name": DEFAULT_MODEL_NAME,
        "model_path": str(model_path),
        "pipeline_type": type(model).__name__,
        "classifier_type": type(classifier).__name__,
        "input_feature_count": len(get_model_input_features()),
        "transformed_feature_count": len(
            get_transformed_feature_names()
        ),
    }
