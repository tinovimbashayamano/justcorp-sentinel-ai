from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
import shap

from backend.app.explainability.explanation_formatter import (
    create_human_summary,
    determine_impact_direction,
    determine_impact_strength,
)
from backend.app.explainability.feature_mapper import (
    map_transformed_features,
)
from backend.app.services.fraud_scoring_service import (
    FRAUD_THRESHOLD,
    assign_risk_band,
    prepare_feature_frame,
)
from backend.app.services.model_registry import (
    DEFAULT_MODEL_NAME,
    get_fraud_classifier,
    get_fraud_model,
    get_fraud_preprocessor,
    get_model_input_features,
    get_transformed_feature_names,
)


class ExplainabilityError(RuntimeError):
    """Raised when a fraud prediction cannot be explained."""


@lru_cache(maxsize=1)
def get_shap_explainer():
    """
    Create and cache one SHAP explainer for the shared classifier.
    """
    classifier = get_fraud_classifier()

    try:
        return shap.TreeExplainer(classifier)
    except Exception as exc:
        raise ExplainabilityError(
            "Unable to initialise the SHAP TreeExplainer."
        ) from exc


def clear_explainer_cache() -> None:
    get_shap_explainer.cache_clear()


def transform_feature_frame(
    feature_frame: pd.DataFrame,
) -> np.ndarray:
    preprocessor = get_fraud_preprocessor()

    try:
        transformed = preprocessor.transform(feature_frame)
    except Exception as exc:
        raise ExplainabilityError(
            "Unable to transform transaction features."
        ) from exc

    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()

    transformed_array = np.asarray(transformed)

    if transformed_array.ndim == 1:
        transformed_array = transformed_array.reshape(1, -1)

    return transformed_array


def extract_positive_class_shap_values(
    shap_values: Any,
) -> np.ndarray:
    """
    Normalise SHAP outputs across supported SHAP versions.

    Possible binary-classification formats include:

    - list[class_zero_values, class_one_values]
    - ndarray(samples, features)
    - ndarray(samples, features, classes)
    """
    if isinstance(shap_values, list):
        if len(shap_values) == 2:
            return np.asarray(shap_values[1])

        if len(shap_values) == 1:
            return np.asarray(shap_values[0])

        raise ExplainabilityError(
            "Unexpected SHAP class output."
        )

    values = np.asarray(shap_values)

    if values.ndim == 3:
        if values.shape[2] >= 2:
            return values[:, :, 1]

        return values[:, :, 0]

    if values.ndim == 2:
        return values

    if values.ndim == 1:
        return values.reshape(1, -1)

    raise ExplainabilityError(
        "Unsupported SHAP value dimensions."
    )


def extract_positive_class_base_value(
    expected_value: Any,
) -> float:
    values = np.asarray(expected_value)

    if values.ndim == 0:
        return float(values)

    flattened = values.reshape(-1)

    if len(flattened) >= 2:
        return float(flattened[1])

    if len(flattened) == 1:
        return float(flattened[0])

    raise ExplainabilityError(
        "Unable to determine the SHAP base value."
    )


def calculate_shap_values(
    transformed_features: np.ndarray,
) -> tuple[np.ndarray, float]:
    explainer = get_shap_explainer()

    try:
        raw_shap_values = explainer.shap_values(
            transformed_features
        )
    except Exception as exc:
        raise ExplainabilityError(
            "Unable to calculate SHAP values."
        ) from exc

    positive_values = extract_positive_class_shap_values(
        raw_shap_values
    )

    base_value = extract_positive_class_base_value(
        explainer.expected_value
    )

    return positive_values, base_value


def build_feature_contributions(
    transformed_values: np.ndarray,
    shap_values: np.ndarray,
    top_n: int,
) -> list[dict[str, Any]]:
    transformed_feature_names = (
        get_transformed_feature_names()
    )
    raw_feature_names = get_model_input_features()

    if shap_values.ndim != 2 or len(shap_values) != 1:
        raise ExplainabilityError(
            "A local explanation requires exactly one transaction."
        )

    if transformed_values.ndim != 2 or len(
        transformed_values
    ) != 1:
        raise ExplainabilityError(
            "Transformed features must contain one transaction."
        )

    transaction_shap_values = shap_values[0]
    transaction_feature_values = transformed_values[0]

    if len(transaction_shap_values) != len(
        transformed_feature_names
    ):
        raise ExplainabilityError(
            "SHAP feature count does not match the model's "
            "transformed feature count."
        )

    feature_descriptors = map_transformed_features(
        transformed_names=transformed_feature_names,
        raw_feature_names=raw_feature_names,
    )

    sorted_indices = np.argsort(
        np.abs(transaction_shap_values)
    )[::-1]

    selected_indices = sorted_indices[:top_n]

    maximum_absolute_value = (
        float(
            np.max(
                np.abs(transaction_shap_values)
            )
        )
        if len(transaction_shap_values)
        else 0.0
    )

    contributions: list[dict[str, Any]] = []

    for rank, feature_index in enumerate(
        selected_indices,
        start=1,
    ):
        descriptor = feature_descriptors[
            int(feature_index)
        ]

        shap_value = float(
            transaction_shap_values[feature_index]
        )

        feature_value = transaction_feature_values[
            feature_index
        ]

        if isinstance(feature_value, np.generic):
            feature_value = feature_value.item()

        absolute_shap_value = abs(shap_value)

        contributions.append(
            {
                "rank": rank,
                "transformed_feature": (
                    descriptor.transformed_name
                ),
                "source_feature": (
                    descriptor.source_feature
                ),
                "category": descriptor.category,
                "display_name": descriptor.display_name,
                "feature_value": feature_value,
                "shap_value": shap_value,
                "absolute_shap_value": (
                    absolute_shap_value
                ),
                "impact_direction": (
                    determine_impact_direction(
                        shap_value
                    )
                ),
                "impact_strength": (
                    determine_impact_strength(
                        absolute_shap_value,
                        maximum_absolute_value,
                    )
                ),
            }
        )

    return contributions


def explain_transaction(
    features: dict[str, Any],
    top_n: int = 10,
) -> dict[str, Any]:
    if top_n < 1:
        raise ValueError(
            "top_n must be greater than zero."
        )

    model = get_fraud_model()
    expected_columns = get_model_input_features()

    feature_frame, feature_quality = (
        prepare_feature_frame(
            features=features,
            expected_columns=expected_columns,
        )
    )

    try:
        fraud_probability = float(
            model.predict_proba(feature_frame)[0, 1]
        )
    except Exception as exc:
        raise ExplainabilityError(
            "Unable to calculate the fraud probability."
        ) from exc

    transformed_values = transform_feature_frame(
        feature_frame
    )

    shap_values, base_value = calculate_shap_values(
        transformed_values
    )

    contributions = build_feature_contributions(
        transformed_values=transformed_values,
        shap_values=shap_values,
        top_n=top_n,
    )

    fraud_prediction = int(
        fraud_probability >= FRAUD_THRESHOLD
    )

    return {
        "model_name": DEFAULT_MODEL_NAME,
        "explanation_type": "local",
        "fraud_probability": fraud_probability,
        "fraud_prediction": fraud_prediction,
        "fraud_threshold": FRAUD_THRESHOLD,
        "risk_band": assign_risk_band(
            fraud_probability
        ),
        "base_value": base_value,
        "top_feature_count": len(contributions),
        "feature_contributions": contributions,
        "feature_quality": feature_quality,
        "summary": create_human_summary(
            fraud_probability=fraud_probability,
            top_features=contributions,
        ),
    }


def get_explainability_health() -> dict[str, Any]:
    model = get_fraud_model()
    classifier = get_fraud_classifier()
    explainer = get_shap_explainer()

    return {
        "status": "ready",
        "model_name": DEFAULT_MODEL_NAME,
        "pipeline_type": type(model).__name__,
        "classifier_type": type(classifier).__name__,
        "explainer_type": type(explainer).__name__,
        "raw_feature_count": len(
            get_model_input_features()
        ),
        "transformed_feature_count": len(
            get_transformed_feature_names()
        ),
    }
