"""FastAPI endpoints for fraud-case report generation and management."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_active_user
from backend.app.core.reporting import ReportFormat, ReportStatus, ReportType
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.report import (
    GeneratedReportListResponse,
    GeneratedReportResponse,
    ReportDeleteResponse,
    ReportFileIntegrityResponse,
    ReportGenerationAcceptedResponse,
    ReportGenerationRequest,
    ReportListQuery,
    ReportRestoreResponse,
)
from backend.app.services.report_data_service import (
    ReportCaseNotFoundError,
    ReportDataPermissionError,
    UnsupportedReportTypeError,
)
from backend.app.services.report_export_service import (
    InvalidReportPayloadError,
    ReportExportError,
    ReportStorageError,
    UnsupportedExportFormatError,
)
from backend.app.services.reporting_service import (
    GeneratedReportNotFoundError,
    GeneratedReportPermissionError,
    GeneratedReportUnavailableError,
    ReportingService,
    ReportingServiceError,
)


router = APIRouter(
    prefix="/reports",
    tags=["Fraud Case Reports"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedUser = Annotated[User, Depends(get_current_active_user)]

REPORT_READ_ROLES = frozenset(
    {
        "admin",
        "fraud_analyst",
        "risk_manager",
        "manager",
        "auditor",
    }
)
REPORT_GENERATION_ROLES = frozenset(
    {
        "admin",
        "fraud_analyst",
        "risk_manager",
        "manager",
        "auditor",
    }
)
REPORT_DELETE_ROLES = frozenset({"admin"})
REPORT_RESTORE_ROLES = frozenset({"admin"})
REPORT_INTEGRITY_ROLES = frozenset({"admin", "auditor"})


def _normalize_role(current_user: User) -> str:
    """Extract and normalize the authenticated user's role."""

    role = getattr(current_user, "role", None)
    if role is None:
        role = getattr(current_user, "user_role", None)
    if hasattr(role, "value"):
        role = role.value
    if hasattr(role, "name") and not isinstance(role, str):
        role = role.name
    return str(role or "").strip().lower()


def _user_id(current_user: User) -> int | None:
    """Return the authenticated user's database identifier."""

    value = getattr(current_user, "id", None)
    return None if value is None else int(value)


def _username(current_user: User) -> str | None:
    """Return a stable username for report ownership metadata."""

    for attribute_name in ("username", "email", "full_name", "name"):
        value = getattr(current_user, attribute_name, None)
        if value:
            return str(value)
    return None


def _require_role(
    current_user: User,
    allowed_roles: frozenset[str],
) -> str:
    """Ensure the current user has one of the permitted roles."""

    role = _normalize_role(current_user)
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this operation.",
        )
    return role


def _raise_service_exception(exc: Exception) -> None:
    """Convert service exceptions to stable API responses."""

    if isinstance(
        exc,
        (ReportCaseNotFoundError, GeneratedReportNotFoundError),
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (ReportDataPermissionError, GeneratedReportPermissionError),
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if isinstance(
        exc,
        (
            GeneratedReportUnavailableError,
            UnsupportedReportTypeError,
            UnsupportedExportFormatError,
            InvalidReportPayloadError,
        ),
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ReportStorageError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report storage is currently unavailable.",
        ) from exc

    if isinstance(exc, (ReportExportError, ReportingServiceError)):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The report operation failed.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected reporting error occurred.",
    ) from exc


@router.post(
    "/cases/{case_id}",
    response_model=ReportGenerationAcceptedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a fraud-case report",
    responses={
        403: {"description": "Insufficient reporting permissions."},
        404: {"description": "Fraud case not found."},
        409: {"description": "Unsupported report configuration."},
        500: {"description": "Report generation failed."},
        503: {"description": "Report storage unavailable."},
    },
)
def generate_case_report(
    case_id: int,
    request: ReportGenerationRequest,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> ReportGenerationAcceptedResponse:
    """Generate and persist a report for one fraud case."""

    requester_role = _require_role(current_user, REPORT_GENERATION_ROLES)
    try:
        service = ReportingService(db)
        report = service.generate_report(
            case_id=case_id,
            request=request,
            requester_user_id=_user_id(current_user),
            requester_username=_username(current_user),
            requester_role=requester_role,
        )
        return ReportGenerationAcceptedResponse(
            message="Report generated successfully.",
            report=service.to_response(report),
        )
    except Exception as exc:
        _raise_service_exception(exc)
        raise


@router.get(
    "/cases/{case_id}",
    response_model=GeneratedReportListResponse,
    summary="List reports for a fraud case",
)
def list_case_reports(
    case_id: int,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
    report_type: ReportType | None = Query(default=None),
    export_format: ReportFormat | None = Query(default=None),
    report_status: ReportStatus | None = Query(default=None, alias="status"),
    include_deleted: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> GeneratedReportListResponse:
    """List generated reports associated with one case."""

    role = _require_role(current_user, REPORT_READ_ROLES)
    if include_deleted and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator may view deleted reports.",
        )

    try:
        query = ReportListQuery(
            report_type=report_type,
            export_format=export_format,
            status=report_status,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )
        return ReportingService(db).list_reports(case_id=case_id, query=query)
    except Exception as exc:
        _raise_service_exception(exc)
        raise


@router.get(
    "",
    response_model=GeneratedReportListResponse,
    summary="List generated reports",
)
def list_all_reports(
    db: DatabaseSession,
    current_user: AuthenticatedUser,
    report_type: ReportType | None = Query(default=None),
    export_format: ReportFormat | None = Query(default=None),
    report_status: ReportStatus | None = Query(default=None, alias="status"),
    include_deleted: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> GeneratedReportListResponse:
    """List generated reports across accessible fraud cases."""

    role = _require_role(current_user, REPORT_READ_ROLES)
    if include_deleted and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator may view deleted reports.",
        )

    try:
        query = ReportListQuery(
            report_type=report_type,
            export_format=export_format,
            status=report_status,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )
        return ReportingService(db).list_reports(query=query)
    except Exception as exc:
        _raise_service_exception(exc)
        raise


@router.get(
    "/{report_id}",
    response_model=GeneratedReportResponse,
    summary="Get generated-report metadata",
)
def get_generated_report(
    report_id: int,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
    include_deleted: bool = Query(default=False),
) -> GeneratedReportResponse:
    """Return detailed metadata for one generated report."""

    role = _require_role(current_user, REPORT_READ_ROLES)
    if include_deleted and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an administrator may view deleted reports.",
        )

    try:
        service = ReportingService(db)
        report = service.get_report(
            report_id=report_id,
            include_deleted=include_deleted,
        )
        return service.to_response(report)
    except Exception as exc:
        _raise_service_exception(exc)
        raise


@router.get(
    "/{report_id}/download",
    response_class=FileResponse,
    summary="Download a generated report",
    responses={
        200: {
            "content": {
                "application/json": {},
                "text/csv": {},
                "application/pdf": {},
            },
            "description": "Generated report file.",
        },
        404: {"description": "Report not found."},
        409: {"description": "Report unavailable or integrity check failed."},
    },
)
def download_generated_report(
    report_id: int,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> FileResponse:
    """Validate report integrity and return the generated file."""

    _require_role(current_user, REPORT_READ_ROLES)
    try:
        metadata = ReportingService(db).prepare_download(report_id=report_id)
        return FileResponse(
            path=Path(metadata.storage_path),
            media_type=metadata.mime_type,
            filename=metadata.filename,
            headers={
                "X-Report-ID": str(metadata.report_id),
                "X-Fraud-Case-ID": str(metadata.case_id),
                "X-Report-SHA256": metadata.sha256_hash,
                "Cache-Control": "private, no-store, no-cache, must-revalidate",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff",
            },
        )
    except Exception as exc:
        _raise_service_exception(exc)
        raise


@router.get(
    "/{report_id}/integrity",
    response_model=ReportFileIntegrityResponse,
    summary="Verify generated-report integrity",
)
def verify_generated_report_integrity(
    report_id: int,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> ReportFileIntegrityResponse:
    """Verify file existence, size and SHA-256 hash."""

    _require_role(current_user, REPORT_INTEGRITY_ROLES)
    try:
        return ReportingService(db).verify_report_integrity(
            report_id=report_id
        )
    except Exception as exc:
        _raise_service_exception(exc)
        raise


@router.delete(
    "/{report_id}",
    response_model=ReportDeleteResponse,
    summary="Delete a generated report",
)
def delete_generated_report(
    report_id: int,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
    remove_file: bool = Query(default=True),
) -> ReportDeleteResponse:
    """Soft delete a generated report."""

    requester_role = _require_role(current_user, REPORT_DELETE_ROLES)
    try:
        return ReportingService(db).soft_delete_report(
            report_id=report_id,
            requester_user_id=_user_id(current_user),
            requester_username=_username(current_user),
            requester_role=requester_role,
            remove_file=remove_file,
        )
    except Exception as exc:
        _raise_service_exception(exc)
        raise


@router.post(
    "/{report_id}/restore",
    response_model=ReportRestoreResponse,
    summary="Restore a deleted generated report",
)
def restore_generated_report(
    report_id: int,
    db: DatabaseSession,
    current_user: AuthenticatedUser,
) -> ReportRestoreResponse:
    """Restore a soft-deleted generated report."""

    requester_role = _require_role(current_user, REPORT_RESTORE_ROLES)
    try:
        service = ReportingService(db)
        report = service.restore_report(
            report_id=report_id,
            requester_role=requester_role,
        )
        return ReportRestoreResponse(
            message="Report restored successfully.",
            report=service.to_response(report),
        )
    except Exception as exc:
        _raise_service_exception(exc)
        raise
