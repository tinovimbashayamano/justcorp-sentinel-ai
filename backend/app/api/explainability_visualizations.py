"""API routes for SHAP visualization data, plots, and reports."""

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.core.dependencies import (
    AdminAnalystOrAuditor,
    AdminOrAnalyst,
    AnyAuthenticatedUser,
)
from backend.app.schemas.explainability_visualization import (
    DependencePlotResponse,
    GlobalPlotImageResponse,
    GlobalVisualizationData,
    InvestigationReportRequest,
    InvestigationReportResponse,
    LocalVisualizationData,
    PlotImageResponse,
    VisualizationHealthResponse,
    VisualizationRequest,
)
from backend.app.services.explainability_visualization_service import (
    VisualizationServiceError,
    explainability_visualization_service,
)


router = APIRouter(
    prefix="/api/v1/explainability-visualizations",
    tags=["Explainability Visualizations"],
)


def _service_unavailable(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(error),
    )


@router.get(
    "/health",
    response_model=VisualizationHealthResponse,
)
def health(
    _: AnyAuthenticatedUser,
) -> VisualizationHealthResponse:
    """Return plotting, export, and explainability readiness."""

    return explainability_visualization_service.health()


@router.post(
    "/local/data",
    response_model=LocalVisualizationData,
)
def local_data(
    payload: VisualizationRequest,
    _: AdminOrAnalyst,
) -> LocalVisualizationData:
    """Return plot-ready local SHAP contributions."""

    try:
        return (
            explainability_visualization_service
            .local_visualization_data(
                payload.transaction_id,
                payload.features,
                payload.top_features,
            )
        )
    except VisualizationServiceError as error:
        raise _service_unavailable(error) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/local/waterfall",
    response_model=PlotImageResponse,
)
def waterfall(
    payload: VisualizationRequest,
    _: AdminOrAnalyst,
) -> PlotImageResponse:
    """Render a local contribution waterfall as a PNG."""

    try:
        return explainability_visualization_service.waterfall_plot(
            payload.transaction_id,
            payload.features,
            payload.top_features,
        )
    except VisualizationServiceError as error:
        raise _service_unavailable(error) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/local/force",
    response_model=PlotImageResponse,
)
def force(
    payload: VisualizationRequest,
    _: AdminOrAnalyst,
) -> PlotImageResponse:
    """Render the cumulative local explanation path as a PNG."""

    try:
        return explainability_visualization_service.force_plot(
            payload.transaction_id,
            payload.features,
            payload.top_features,
        )
    except VisualizationServiceError as error:
        raise _service_unavailable(error) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/global/data",
    response_model=GlobalVisualizationData,
)
def global_data(
    _: AdminAnalystOrAuditor,
    limit: int = Query(20, ge=1, le=100),
) -> GlobalVisualizationData:
    """Return plot-ready global feature importance."""

    try:
        return (
            explainability_visualization_service
            .global_visualization_data(limit)
        )
    except VisualizationServiceError as error:
        raise _service_unavailable(error) from error


@router.get(
    "/global/summary",
    response_model=GlobalPlotImageResponse,
)
def global_summary(
    _: AdminAnalystOrAuditor,
    limit: int = Query(20, ge=1, le=100),
) -> GlobalPlotImageResponse:
    """Render global feature importance as a PNG."""

    try:
        return (
            explainability_visualization_service
            .global_summary_plot(limit)
        )
    except VisualizationServiceError as error:
        raise _service_unavailable(error) from error


@router.get(
    "/dependence/{feature_name}",
    response_model=DependencePlotResponse,
)
def dependence(
    feature_name: str,
    _: AdminAnalystOrAuditor,
    limit: int = Query(500, ge=1, le=5000),
) -> DependencePlotResponse:
    """Return feature-value and SHAP-value pairs."""

    try:
        return explainability_visualization_service.dependence_data(
            feature_name,
            limit,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown transformed model feature: {feature_name}.",
        ) from error
    except VisualizationServiceError as error:
        raise _service_unavailable(error) from error


@router.post(
    "/reports/{report_format}",
    response_model=InvestigationReportResponse,
)
def report(
    report_format: str,
    payload: InvestigationReportRequest,
    _: AdminOrAnalyst,
) -> InvestigationReportResponse:
    """Export an HTML or PDF investigation explanation report."""

    try:
        return explainability_visualization_service.export_report(
            report_format,
            transaction_id=payload.transaction_id,
            features=payload.features,
            top_features=payload.top_features,
            case_id=payload.case_id,
            analyst_notes=payload.analyst_notes,
            include_global_context=(
                payload.include_global_context
            ),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except VisualizationServiceError as error:
        raise _service_unavailable(error) from error
