"""Global SHAP model insights for the production fraud classifier."""

from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np
import pandas as pd

from backend.app.explainability.shap_engine import (
    calculate_shap_values,
    transform_feature_frame,
)
from backend.app.explainability.feature_mapper import (
    remove_transformer_prefix,
)
from backend.app.schemas.model_insights import (
    FeatureDetailResponse,
    FeatureImportance,
    GlobalImportanceResponse,
    InsightHealthResponse,
    TopFeaturesResponse,
)
from backend.app.services.model_registry import (
    PROJECT_ROOT,
    get_fraud_model,
    get_model_input_features,
    get_transformed_feature_names,
)


DEFAULT_DATASET_PATH = (
    "data/processed/baseline_modeling_dataset.csv.gz"
)
DEFAULT_SAMPLE_SIZE = 5_000
DEFAULT_RANDOM_STATE = 42
MODEL_DISPLAY_NAME = "LightGBM"
SUPPORTED_RANKING_SORTS = {"importance", "feature"}


class ModelInsightError(RuntimeError):
    """Raised when global model insights cannot be produced."""


class ModelInsightNotFoundError(ModelInsightError):
    """Raised when a requested transformed feature does not exist."""


class ModelInsightValidationError(ModelInsightError):
    """Raised when model insight options are invalid."""


@dataclass(frozen=True)
class ModelInsightCache:
    """An immutable snapshot of one global SHAP calculation."""

    generated_at: datetime
    samples: int
    feature_names: tuple[str, ...]
    transformed_values: np.ndarray
    shap_values: np.ndarray
    mean_abs_shap: np.ndarray
    positive_effects: np.ndarray
    negative_effects: np.ndarray
    positive_importance: np.ndarray
    negative_importance: np.ndarray
    ranked_indices: np.ndarray
    feature_indices: dict[str, int]
    feature_ranks: dict[str, int]


def _read_positive_integer(
    variable_name: str,
    default: int,
) -> int:
    raw_value = os.getenv(variable_name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ModelInsightValidationError(
            f"{variable_name} must be an integer."
        ) from exc

    if value < 1:
        raise ModelInsightValidationError(
            f"{variable_name} must be greater than zero."
        )

    return value


def resolve_insight_dataset_path(
    configured_path: str | None = None,
) -> Path:
    """Resolve the modelling dataset used for global explanations."""

    raw_path = (
        configured_path
        or os.getenv("MODEL_INSIGHT_DATASET_PATH")
        or os.getenv("MODEL_INSIGHTS_DATASET_PATH")
        or DEFAULT_DATASET_PATH
    )
    dataset_path = Path(raw_path)

    if dataset_path.is_absolute():
        return dataset_path

    return PROJECT_ROOT / dataset_path


def load_insight_sample(
    *,
    dataset_path: str | Path | None = None,
    sample_size: int | None = None,
    random_state: int | None = None,
) -> pd.DataFrame:
    """
    Load and deterministically sample raw model inputs.

    Only the model's expected columns are read, which keeps memory usage
    bounded below that of loading the complete modelling table.
    """

    resolved_path = resolve_insight_dataset_path(
        str(dataset_path) if dataset_path is not None else None
    )

    if not resolved_path.is_file():
        raise ModelInsightError(
            "Model insight dataset was not found: "
            f"{resolved_path}."
        )

    requested_samples = (
        sample_size
        if sample_size is not None
        else _read_positive_integer(
            "MODEL_INSIGHT_SAMPLE_SIZE",
            DEFAULT_SAMPLE_SIZE,
        )
    )

    if requested_samples < 1:
        raise ModelInsightValidationError(
            "sample_size must be greater than zero."
        )

    seed = (
        random_state
        if random_state is not None
        else _read_positive_integer(
            "MODEL_INSIGHT_RANDOM_STATE",
            DEFAULT_RANDOM_STATE,
        )
    )
    expected_columns = get_model_input_features()

    try:
        header = pd.read_csv(resolved_path, nrows=0)
    except Exception as exc:
        raise ModelInsightError(
            "Unable to read the model insight dataset header."
        ) from exc

    missing_columns = sorted(
        set(expected_columns) - set(header.columns)
    )

    if missing_columns:
        preview = ", ".join(missing_columns[:10])
        raise ModelInsightError(
            "Model insight dataset is missing required model "
            f"features: {preview}."
        )

    try:
        feature_frame = pd.read_csv(
            resolved_path,
            usecols=expected_columns,
        )
    except Exception as exc:
        raise ModelInsightError(
            "Unable to load the model insight dataset."
        ) from exc

    if feature_frame.empty:
        raise ModelInsightError(
            "Model insight dataset contains no samples."
        )

    actual_sample_size = min(
        requested_samples,
        len(feature_frame),
    )

    if actual_sample_size < len(feature_frame):
        feature_frame = feature_frame.sample(
            n=actual_sample_size,
            random_state=seed,
        )

    return feature_frame.reset_index(drop=True)


def _validate_matrix(
    values: Any,
    *,
    name: str,
) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)

    if matrix.ndim == 1:
        matrix = matrix.reshape(1, -1)

    if matrix.ndim != 2:
        raise ModelInsightError(
            f"{name} must be a two-dimensional matrix."
        )

    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ModelInsightError(
            f"{name} must not be empty."
        )

    if not np.all(np.isfinite(matrix)):
        raise ModelInsightError(
            f"{name} contains non-finite values."
        )

    return matrix


def calculate_feature_effects(
    shap_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate global importance and directional sample percentages.
    """

    values = _validate_matrix(
        shap_values,
        name="SHAP values",
    )
    mean_abs_shap = np.mean(np.abs(values), axis=0)

    positive_effects = np.mean(values > 0, axis=0) * 100
    negative_effects = np.mean(values < 0, axis=0) * 100

    return mean_abs_shap, positive_effects, negative_effects


def calculate_directional_importance(
    shap_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return prevalence-weighted positive and negative SHAP magnitudes."""

    values = _validate_matrix(
        shap_values,
        name="SHAP values",
    )

    return (
        np.mean(np.clip(values, 0.0, None), axis=0),
        np.mean(np.clip(-values, 0.0, None), axis=0),
    )


def create_public_feature_names(
    transformed_names: list[str],
) -> list[str]:
    """Remove transformer prefixes while retaining unique feature names."""

    stripped_names = [
        remove_transformer_prefix(name)
        for name in transformed_names
    ]
    name_counts = Counter(stripped_names)

    return [
        (
            stripped_name
            if name_counts[stripped_name] == 1
            else transformed_name
        )
        for transformed_name, stripped_name in zip(
            transformed_names,
            stripped_names,
            strict=True,
        )
    ]


def build_insight_cache(
    feature_frame: pd.DataFrame | None = None,
) -> ModelInsightCache:
    """Build a complete, internally consistent global insight snapshot."""

    # Resolve these first so model-loading failures receive service context.
    try:
        get_fraud_model()
        transformed_feature_names = (
            get_transformed_feature_names()
        )
        feature_names = create_public_feature_names(
            transformed_feature_names
        )
        sample = (
            feature_frame.copy()
            if feature_frame is not None
            else load_insight_sample()
        )
    except ModelInsightError:
        raise
    except Exception as exc:
        raise ModelInsightError(
            "Unable to load the fraud model or insight sample."
        ) from exc

    if sample.empty:
        raise ModelInsightError(
            "At least one sample is required for model insights."
        )

    try:
        transformed_values = _validate_matrix(
            transform_feature_frame(sample),
            name="Transformed feature values",
        )
        shap_values, _ = calculate_shap_values(
            transformed_values
        )
        shap_matrix = _validate_matrix(
            shap_values,
            name="SHAP values",
        )
    except ModelInsightError:
        raise
    except Exception as exc:
        raise ModelInsightError(
            "Unable to calculate global SHAP values."
        ) from exc

    expected_shape = (
        transformed_values.shape[0],
        len(transformed_feature_names),
    )

    if transformed_values.shape != expected_shape:
        raise ModelInsightError(
            "Transformed feature count does not match the model's "
            "feature names."
        )

    if shap_matrix.shape != expected_shape:
        raise ModelInsightError(
            "SHAP output shape does not match the transformed "
            "feature matrix."
        )

    if len(set(feature_names)) != len(feature_names):
        raise ModelInsightError(
            "Transformed model feature names must be unique."
        )

    (
        mean_abs_shap,
        positive_effects,
        negative_effects,
    ) = calculate_feature_effects(shap_matrix)
    (
        positive_importance,
        negative_importance,
    ) = calculate_directional_importance(shap_matrix)

    # Stable sorting keeps model feature order deterministic for ties.
    ranked_indices = np.argsort(
        -mean_abs_shap,
        kind="stable",
    )
    feature_indices = {
        feature: index
        for index, feature in enumerate(
            feature_names
        )
    }
    feature_ranks = {
        feature_names[int(index)]: rank
        for rank, index in enumerate(
            ranked_indices,
            start=1,
        )
    }

    # Cached arrays are read-only so every endpoint observes one snapshot.
    for array in (
        transformed_values,
        shap_matrix,
        mean_abs_shap,
        positive_effects,
        negative_effects,
        positive_importance,
        negative_importance,
        ranked_indices,
    ):
        array.setflags(write=False)

    return ModelInsightCache(
        generated_at=datetime.now(timezone.utc),
        samples=transformed_values.shape[0],
        feature_names=tuple(feature_names),
        transformed_values=transformed_values,
        shap_values=shap_matrix,
        mean_abs_shap=mean_abs_shap,
        positive_effects=positive_effects,
        negative_effects=negative_effects,
        positive_importance=positive_importance,
        negative_importance=negative_importance,
        ranked_indices=ranked_indices,
        feature_indices=feature_indices,
        feature_ranks=feature_ranks,
    )


class ModelInsightService:
    """Application service for cached, global model explainability."""

    def __init__(self) -> None:
        self._cache: ModelInsightCache | None = None
        self._cache_lock = RLock()

    def _get_cache(self) -> ModelInsightCache:
        cache = self._cache

        if cache is not None:
            return cache

        with self._cache_lock:
            if self._cache is None:
                self._cache = build_insight_cache()

            return self._cache

    @staticmethod
    def _validate_limit(
        limit: int | None,
        feature_count: int,
    ) -> int:
        if limit is None:
            return feature_count

        if limit < 1:
            raise ModelInsightValidationError(
                "limit must be greater than zero."
            )

        return min(limit, feature_count)

    @staticmethod
    def _importance_item(
        cache: ModelInsightCache,
        feature_index: int,
        importance: float,
        *,
        rank: int | None = None,
    ) -> FeatureImportance:
        feature_name = cache.feature_names[feature_index]

        return FeatureImportance(
            rank=(
                rank
                if rank is not None
                else cache.feature_ranks[feature_name]
            ),
            feature=feature_name,
            importance=float(importance),
        )

    def get_global_importance(
        self,
        *,
        limit: int | None = None,
    ) -> GlobalImportanceResponse:
        cache = self._get_cache()
        resolved_limit = self._validate_limit(
            limit,
            len(cache.feature_names),
        )
        selected = cache.ranked_indices[:resolved_limit]

        return GlobalImportanceResponse(
            generated_at=cache.generated_at,
            samples=cache.samples,
            features=[
                self._importance_item(
                    cache,
                    int(feature_index),
                    cache.mean_abs_shap[feature_index],
                )
                for feature_index in selected
            ],
        )

    def compute_global_importance(
        self,
    ) -> GlobalImportanceResponse:
        """Return the cached global mean-absolute-SHAP ranking."""

        return self.get_global_importance()

    def get_feature_rankings(
        self,
        *,
        limit: int = 20,
        sort: str = "importance",
    ) -> GlobalImportanceResponse:
        """Return a limited ranking sorted by importance or feature name."""

        cache = self._get_cache()
        normalized_sort = sort.strip().lower()

        if normalized_sort not in SUPPORTED_RANKING_SORTS:
            supported = ", ".join(
                sorted(SUPPORTED_RANKING_SORTS)
            )
            raise ModelInsightValidationError(
                f"sort must be one of: {supported}."
            )

        resolved_limit = self._validate_limit(
            limit,
            len(cache.feature_names),
        )

        if normalized_sort == "importance":
            selected = cache.ranked_indices[:resolved_limit]
        else:
            selected = np.asarray(
                sorted(
                    range(len(cache.feature_names)),
                    key=lambda index: (
                        cache.feature_names[index].casefold()
                    ),
                )[:resolved_limit],
                dtype=int,
            )

        return GlobalImportanceResponse(
            generated_at=cache.generated_at,
            samples=cache.samples,
            features=[
                self._importance_item(
                    cache,
                    int(feature_index),
                    cache.mean_abs_shap[feature_index],
                )
                for feature_index in selected
            ],
        )

    def get_feature_detail(
        self,
        feature: str,
    ) -> FeatureDetailResponse:
        cache = self._get_cache()
        feature_index = cache.feature_indices.get(feature)

        if feature_index is None:
            raise ModelInsightNotFoundError(
                f"Unknown transformed model feature: {feature}."
            )

        values = cache.transformed_values[:, feature_index]

        return FeatureDetailResponse(
            feature=feature,
            rank=cache.feature_ranks[feature],
            mean_abs_shap=float(
                cache.mean_abs_shap[feature_index]
            ),
            positive_effect=round(
                float(cache.positive_effects[feature_index]),
                6,
            ),
            negative_effect=round(
                float(cache.negative_effects[feature_index]),
                6,
            ),
            minimum=float(np.min(values)),
            maximum=float(np.max(values)),
            mean=float(np.mean(values)),
            median=float(np.median(values)),
        )

    def get_feature(
        self,
        feature_name: str,
    ) -> FeatureDetailResponse:
        """Look up one feature by its public model feature name."""

        return self.get_feature_detail(feature_name)

    def get_top_features(
        self,
        direction: str,
        *,
        limit: int = 10,
    ) -> TopFeaturesResponse:
        cache = self._get_cache()
        normalized_direction = direction.strip().lower()

        if normalized_direction not in {"positive", "negative"}:
            raise ModelInsightValidationError(
                "direction must be 'positive' or 'negative'."
            )

        resolved_limit = self._validate_limit(
            limit,
            len(cache.feature_names),
        )

        if normalized_direction == "positive":
            effect_values = cache.positive_importance
            eligible = np.flatnonzero(effect_values > 0)
            sorted_indices = eligible[
                np.argsort(
                    -effect_values[eligible],
                    kind="stable",
                )
            ]
        else:
            effect_values = cache.negative_importance
            eligible = np.flatnonzero(effect_values > 0)
            sorted_indices = eligible[
                np.argsort(
                    -effect_values[eligible],
                    kind="stable",
                )
            ]

        selected = sorted_indices[:resolved_limit]

        return TopFeaturesResponse(
            generated_at=cache.generated_at,
            direction=normalized_direction,
            features=[
                self._importance_item(
                    cache,
                    int(feature_index),
                    effect_values[feature_index],
                    rank=rank,
                )
                for rank, feature_index in enumerate(
                    selected,
                    start=1,
                )
            ],
        )

    def get_top_positive_features(
        self,
        *,
        limit: int = 10,
    ) -> TopFeaturesResponse:
        return self.get_top_features(
            "positive",
            limit=limit,
        )

    def top_positive(
        self,
        *,
        limit: int = 20,
    ) -> TopFeaturesResponse:
        return self.get_top_positive_features(limit=limit)

    def get_top_negative_features(
        self,
        *,
        limit: int = 10,
    ) -> TopFeaturesResponse:
        return self.get_top_features(
            "negative",
            limit=limit,
        )

    def top_negative(
        self,
        *,
        limit: int = 20,
    ) -> TopFeaturesResponse:
        return self.get_top_negative_features(limit=limit)

    def refresh_cache(self) -> GlobalImportanceResponse:
        """
        Recompute insights and atomically replace the previous snapshot.

        The old snapshot remains available if recomputation fails.
        """

        with self._cache_lock:
            refreshed_cache = build_insight_cache()
            self._cache = refreshed_cache

        return self.get_global_importance()

    def get_health(self) -> InsightHealthResponse:
        cache = self._get_cache()

        return InsightHealthResponse(
            status="ready",
            model=MODEL_DISPLAY_NAME,
            samples_used=cache.samples,
            feature_count=len(cache.feature_names),
        )

    # Short aliases support service-oriented API call sites.
    health = get_health
    global_importance = get_global_importance
    feature_detail = get_feature_detail
    top_features = get_top_features
    refresh = refresh_cache


model_insight_service = ModelInsightService()


def get_global_importance(
    *,
    limit: int | None = None,
) -> GlobalImportanceResponse:
    return model_insight_service.get_global_importance(
        limit=limit
    )


def get_feature_detail(
    feature: str,
) -> FeatureDetailResponse:
    return model_insight_service.get_feature_detail(feature)


def get_top_features(
    direction: str,
    *,
    limit: int = 10,
) -> TopFeaturesResponse:
    return model_insight_service.get_top_features(
        direction,
        limit=limit,
    )


def get_top_positive_features(
    *,
    limit: int = 10,
) -> TopFeaturesResponse:
    return model_insight_service.get_top_positive_features(
        limit=limit
    )


def get_top_negative_features(
    *,
    limit: int = 10,
) -> TopFeaturesResponse:
    return model_insight_service.get_top_negative_features(
        limit=limit
    )


def refresh_model_insights() -> GlobalImportanceResponse:
    return model_insight_service.refresh_cache()


def get_model_insight_health() -> InsightHealthResponse:
    return model_insight_service.get_health()
