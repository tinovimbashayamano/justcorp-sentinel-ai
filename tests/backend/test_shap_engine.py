from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from backend.app.explainability import shap_engine


@pytest.fixture(autouse=True)
def clear_shap_cache():
    shap_engine.clear_explainer_cache()
    yield
    shap_engine.clear_explainer_cache()


def test_extract_positive_class_shap_values_from_list():
    negative_class = np.array([[1.0, 2.0]])
    positive_class = np.array([[3.0, 4.0]])

    result = (
        shap_engine.extract_positive_class_shap_values(
            [negative_class, positive_class]
        )
    )

    np.testing.assert_array_equal(
        result,
        positive_class,
    )


def test_extract_positive_class_shap_values_from_3d_array():
    values = np.array(
        [
            [
                [1.0, 2.0],
                [3.0, 4.0],
            ]
        ]
    )

    result = (
        shap_engine.extract_positive_class_shap_values(
            values
        )
    )

    np.testing.assert_array_equal(
        result,
        np.array([[2.0, 4.0]]),
    )


def test_extract_positive_class_base_value():
    result = (
        shap_engine.extract_positive_class_base_value(
            [0.1, 0.9]
        )
    )

    assert result == 0.9


def test_transform_feature_frame_converts_sparse_output(
    monkeypatch,
):
    sparse_output = Mock()
    sparse_output.toarray.return_value = np.array(
        [[1.0, 2.0]]
    )

    preprocessor = Mock()
    preprocessor.transform.return_value = sparse_output

    monkeypatch.setattr(
        shap_engine,
        "get_fraud_preprocessor",
        lambda: preprocessor,
    )

    feature_frame = pd.DataFrame(
        [{"TransactionAmt": 100.0}]
    )

    result = shap_engine.transform_feature_frame(
        feature_frame
    )

    np.testing.assert_array_equal(
        result,
        np.array([[1.0, 2.0]]),
    )


def test_get_shap_explainer_is_cached(
    monkeypatch,
):
    classifier = Mock()
    explainer = Mock()
    tree_explainer = Mock(return_value=explainer)

    monkeypatch.setattr(
        shap_engine,
        "get_fraud_classifier",
        lambda: classifier,
    )
    monkeypatch.setattr(
        shap_engine.shap,
        "TreeExplainer",
        tree_explainer,
    )

    first = shap_engine.get_shap_explainer()
    second = shap_engine.get_shap_explainer()

    assert first is explainer
    assert second is explainer
    tree_explainer.assert_called_once_with(
        classifier
    )


def test_build_feature_contributions_orders_by_impact(
    monkeypatch,
):
    monkeypatch.setattr(
        shap_engine,
        "get_transformed_feature_names",
        lambda: [
            "numeric__TransactionAmt",
            "categorical__ProductCD_W",
            "numeric__card1",
        ],
    )

    monkeypatch.setattr(
        shap_engine,
        "get_model_input_features",
        lambda: [
            "TransactionAmt",
            "ProductCD",
            "card1",
        ],
    )

    transformed_values = np.array(
        [[100.0, 1.0, 1234.0]]
    )

    shap_values = np.array(
        [[0.2, -0.8, 0.4]]
    )

    result = (
        shap_engine.build_feature_contributions(
            transformed_values=transformed_values,
            shap_values=shap_values,
            top_n=2,
        )
    )

    assert len(result) == 2
    assert result[0]["source_feature"] == "ProductCD"
    assert result[0]["category"] == "W"
    assert result[0]["shap_value"] == -0.8
    assert result[0]["impact_direction"] == (
        "decreases_fraud_risk"
    )

    assert result[1]["source_feature"] == "card1"
    assert result[1]["shap_value"] == 0.4


def test_explain_transaction_rejects_invalid_top_n():
    with pytest.raises(
        ValueError,
        match="top_n",
    ):
        shap_engine.explain_transaction(
            features={},
            top_n=0,
        )


def test_explain_transaction_returns_local_explanation(
    monkeypatch,
):
    model = Mock()
    model.predict_proba.return_value = np.array(
        [[0.10, 0.90]]
    )

    monkeypatch.setattr(
        shap_engine,
        "get_fraud_model",
        lambda: model,
    )

    monkeypatch.setattr(
        shap_engine,
        "get_model_input_features",
        lambda: [
            "TransactionAmt",
            "ProductCD",
        ],
    )

    monkeypatch.setattr(
        shap_engine,
        "transform_feature_frame",
        lambda frame: np.array([[100.0, 1.0]]),
    )

    monkeypatch.setattr(
        shap_engine,
        "calculate_shap_values",
        lambda values: (
            np.array([[0.7, -0.2]]),
            -2.0,
        ),
    )

    monkeypatch.setattr(
        shap_engine,
        "build_feature_contributions",
        lambda transformed_values, shap_values, top_n: [
            {
                "rank": 1,
                "transformed_feature": (
                    "numeric__TransactionAmt"
                ),
                "source_feature": "TransactionAmt",
                "category": None,
                "display_name": "TransactionAmt",
                "feature_value": 100.0,
                "shap_value": 0.7,
                "absolute_shap_value": 0.7,
                "impact_direction": (
                    "increases_fraud_risk"
                ),
                "impact_strength": "strong",
            }
        ],
    )

    result = shap_engine.explain_transaction(
        features={
            "TransactionAmt": 100.0,
            "ProductCD": "W",
        },
        top_n=1,
    )

    assert result["model_name"] == (
        "lightgbm_fraud_model"
    )
    assert result["fraud_probability"] == 0.90
    assert result["fraud_prediction"] == 1
    assert result["risk_band"] == "high"
    assert result["base_value"] == -2.0
    assert result["top_feature_count"] == 1
    assert len(result["feature_contributions"]) == 1
