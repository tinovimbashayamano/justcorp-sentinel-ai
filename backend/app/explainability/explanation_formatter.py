from typing import Any


def determine_impact_direction(shap_value: float) -> str:
    if shap_value > 0:
        return "increases_fraud_risk"

    if shap_value < 0:
        return "decreases_fraud_risk"

    return "neutral"


def determine_impact_strength(
    absolute_shap_value: float,
    maximum_absolute_shap_value: float,
) -> str:
    if maximum_absolute_shap_value <= 0:
        return "none"

    relative_strength = (
        absolute_shap_value
        / maximum_absolute_shap_value
    )

    if relative_strength >= 0.67:
        return "strong"

    if relative_strength >= 0.34:
        return "moderate"

    return "weak"


def create_human_summary(
    fraud_probability: float,
    top_features: list[dict[str, Any]],
) -> str:
    risk_increasing = [
        feature["display_name"]
        for feature in top_features
        if feature["impact_direction"]
        == "increases_fraud_risk"
    ]

    risk_decreasing = [
        feature["display_name"]
        for feature in top_features
        if feature["impact_direction"]
        == "decreases_fraud_risk"
    ]

    probability_percent = fraud_probability * 100

    summary_parts = [
        (
            "The model assigned a fraud probability of "
            f"{probability_percent:.2f}%."
        )
    ]

    if risk_increasing:
        summary_parts.append(
            "The strongest factors increasing fraud risk were "
            + ", ".join(risk_increasing[:3])
            + "."
        )

    if risk_decreasing:
        summary_parts.append(
            "Factors reducing fraud risk included "
            + ", ".join(risk_decreasing[:3])
            + "."
        )

    if not risk_increasing and not risk_decreasing:
        summary_parts.append(
            "No material feature contribution was identified."
        )

    return " ".join(summary_parts)
