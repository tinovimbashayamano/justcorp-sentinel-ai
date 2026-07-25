"""Unit tests for cached global model insight calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.app.services import model_insight_service as insight_module
from backend.app.services.model_insight_service import (
    ModelInsightNotFoundError,
    ModelInsightService,
    build_insight_cache,
)


@pytest.fixture
def insight_cache(monkeypatch):
    transformed_values = np.asarray(
        [
            [10.0, 1.0, 3.0],
            [20.0, 2.0, 1.0],
            [30.0, 3.0, 2.0],
            [40.0, 4.0, 4.0],
        ]
    )
    shap_values = np.asarray(
        [
            [0.4, -0.1, 0.2],
            [0.2, -0.3, -0.1],
            [-0.1, -0.2, 0.1],
            [0.3, 0.1, -0.2],
        ]
    )

    monkeypatch.setattr(
        insight_module,
        "get_fraud_model",
        lambda: object(),
    )
    monkeypatch.setattr(
        insight_module,
        "get_transformed_feature_names",
        lambda: [
            "numeric__TransactionAmt",
            "numeric__card1",
            "numeric__C5",
        ],
    )
    monkeypatch.setattr(
        insight_module,
        "transform_feature_frame",
        lambda _: transformed_values,
    )
    monkeypatch.setattr(
        insight_module,
        "calculate_shap_values",
        lambda _: (shap_values, 0.0),
    )

    return build_insight_cache(
        pd.DataFrame({"unused": range(4)})
    )


@pytest.fixture
def service(insight_cache) -> ModelInsightService:
    instance = ModelInsightService()
    instance._cache = insight_cache
    return instance


def test_health_reports_cached_model_dimensions(service):
    response = service.health()

    assert response.status == "ready"
    assert response.model == "LightGBM"
    assert response.samples_used == 4
    assert response.feature_count == 3


def test_cache_is_reused_until_explicit_refresh(
    monkeypatch,
    insight_cache,
):
    build_calls = 0

    def fake_build():
        nonlocal build_calls
        build_calls += 1
        return insight_cache

    monkeypatch.setattr(
        insight_module,
        "build_insight_cache",
        fake_build,
    )
    service = ModelInsightService()

    service.health()
    service.compute_global_importance()
    service.get_feature_rankings()

    assert build_calls == 1

    service.refresh_cache()

    assert build_calls == 2


def test_rankings_use_mean_absolute_shap(service):
    response = service.get_feature_rankings(limit=2)

    assert [item.feature for item in response.features] == [
        "TransactionAmt",
        "card1",
    ]
    assert response.features[0].importance == pytest.approx(0.25)
    assert response.features[1].importance == pytest.approx(0.175)


def test_feature_detail_lookup_returns_flat_statistics(service):
    response = service.get_feature("TransactionAmt")

    assert response.rank == 1
    assert response.mean_abs_shap == pytest.approx(0.25)
    assert response.positive_effect == pytest.approx(75.0)
    assert response.negative_effect == pytest.approx(25.0)
    assert response.minimum == 10.0
    assert response.maximum == 40.0
    assert response.mean == 25.0
    assert response.median == 25.0


def test_invalid_feature_raises_not_found_error(service):
    with pytest.raises(ModelInsightNotFoundError):
        service.get_feature("unknown")


def test_top_positive_features_are_ranked_by_positive_shap(service):
    response = service.top_positive(limit=2)

    assert response.direction == "positive"
    assert response.features[0].feature == "TransactionAmt"
    assert response.features[0].importance == pytest.approx(0.225)


def test_top_negative_features_are_ranked_by_negative_shap(service):
    response = service.top_negative(limit=2)

    assert response.direction == "negative"
    assert response.features[0].feature == "card1"
    assert response.features[0].importance == pytest.approx(0.15)
