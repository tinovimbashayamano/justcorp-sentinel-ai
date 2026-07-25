"""REST endpoints for cached global model explainability insights."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.dependencies import (
    AdminAnalystOrAuditor,
    AnyAuthenticatedUser,
)
from backend.app.schemas.model_insights import (
    FeatureDetailResponse,
    GlobalImportanceResponse,
    InsightHealthResponse,
    TopFeaturesResponse,
)
from backend.app.services.model_insight_service import (
    ModelInsightError,
    ModelInsightNotFoundError,
    ModelInsightService,
    ModelInsightValidationError,
    model_insight_service,
)


router = APIRouter(
    prefix="/api/v1/model-insights",
    tags=["Model Insights"],
)


def get_model_insight_service() -> ModelInsightService:
    """Provide the process-wide cached insight service."""

    return model_insight_service


InsightService = Annotated[
    ModelInsightService,
    Depends(get_model_insight_service),
]


def _translate_service_error(error: ModelInsightError) -> HTTPException:
    if isinstance(error, ModelInsightNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    if isinstance(error, ModelInsightValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        )

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(error),
    )


@router.get(
    "/health",
    response_model=InsightHealthResponse,
    summary="Health",
)
def model_insight_health(
    _: AnyAuthenticatedUser,
    service: InsightService,
) -> InsightHealthResponse:
    """Return model-insight readiness and cached matrix dimensions."""

    try:
        return service.health()
    except ModelInsightError as error:
        raise _translate_service_error(error) from error


@router.get(
    "/global",
    response_model=GlobalImportanceResponse,
    summary="Global Importance",
)
def global_importance(
    _: AdminAnalystOrAuditor,
    service: InsightService,
) -> GlobalImportanceResponse:
    """Return the complete mean-absolute-SHAP feature ranking."""

    try:
        return service.compute_global_importance()
    except ModelInsightError as error:
        raise _translate_service_error(error) from error


@router.get(
    "/features",
    response_model=GlobalImportanceResponse,
    summary="Feature Rankings",
)
def feature_rankings(
    _: AdminAnalystOrAuditor,
    service: InsightService,
    limit: Annotated[int, Query(ge=1, le=1_000)] = 20,
    sort: Annotated[
        Literal["importance", "feature"],
        Query(),
    ] = "importance",
) -> GlobalImportanceResponse:
    """Return a limited feature ranking."""

    try:
        return service.get_feature_rankings(
            limit=limit,
            sort=sort,
        )
    except ModelInsightError as error:
        raise _translate_service_error(error) from error


@router.get(
    "/features/{feature_name}",
    response_model=FeatureDetailResponse,
    summary="Feature Detail",
)
def feature_detail(
    feature_name: str,
    _: AdminAnalystOrAuditor,
    service: InsightService,
) -> FeatureDetailResponse:
    """Return SHAP effects and descriptive statistics for one feature."""

    try:
        return service.get_feature(feature_name)
    except ModelInsightError as error:
        raise _translate_service_error(error) from error


@router.get(
    "/top-positive",
    response_model=TopFeaturesResponse,
    summary="Top Positive",
)
def top_positive(
    _: AdminAnalystOrAuditor,
    service: InsightService,
    limit: Annotated[int, Query(ge=1, le=1_000)] = 20,
) -> TopFeaturesResponse:
    """Return features with the strongest fraud-driving SHAP effects."""

    try:
        return service.top_positive(limit=limit)
    except ModelInsightError as error:
        raise _translate_service_error(error) from error


@router.get(
    "/top-negative",
    response_model=TopFeaturesResponse,
    summary="Top Negative",
)
def top_negative(
    _: AdminAnalystOrAuditor,
    service: InsightService,
    limit: Annotated[int, Query(ge=1, le=1_000)] = 20,
) -> TopFeaturesResponse:
    """Return features with the strongest risk-reducing SHAP effects."""

    try:
        return service.top_negative(limit=limit)
    except ModelInsightError as error:
        raise _translate_service_error(error) from error


@router.post(
    "/refresh-cache",
    response_model=GlobalImportanceResponse,
    summary="Refresh Cache",
)
def refresh_cache(
    _: AdminAnalystOrAuditor,
    service: InsightService,
) -> GlobalImportanceResponse:
    """Explicitly recompute and atomically replace the SHAP cache."""

    try:
        return service.refresh_cache()
    except ModelInsightError as error:
        raise _translate_service_error(error) from error
