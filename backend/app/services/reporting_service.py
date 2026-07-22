"""Lifecycle and persistence service for generated fraud-case reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.reporting import (
    MAX_FAILURE_MESSAGE_LENGTH,
    REPORT_DELETE_ROLES,
    ReportStatus,
)
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.generated_report import GeneratedReport
from backend.app.schemas.report import (
    GeneratedReportListResponse,
    GeneratedReportResponse,
    GeneratedReportSummary,
    ReportDeleteResponse,
    ReportDownloadMetadata,
    ReportFileIntegrityResponse,
    ReportGenerationOptions,
    ReportGenerationRequest,
    ReportListQuery,
)
from backend.app.services.report_data_service import (
    ReportCaseNotFoundError,
    ReportDataService,
)
from backend.app.services.report_export_service import (
    ReportExportError,
    ReportExportService,
)


class ReportingServiceError(RuntimeError):
    """Base generated-report lifecycle error."""


class GeneratedReportNotFoundError(ReportingServiceError):
    """Raised when a generated report does not exist."""


class GeneratedReportUnavailableError(ReportingServiceError):
    """Raised when a report is not available for download."""


class GeneratedReportPermissionError(ReportingServiceError):
    """Raised when a user cannot perform a report operation."""


class ReportingService:
    """Create, query, download, verify and delete generated reports."""

    def __init__(
        self,
        db: Session,
        *,
        data_service: ReportDataService | None = None,
        export_service: ReportExportService | None = None,
    ) -> None:
        self.db = db
        self.data_service = data_service or ReportDataService(db)
        self.export_service = export_service or ReportExportService()

    def generate_report(
        self,
        *,
        case_id: int,
        request: ReportGenerationRequest,
        requester_user_id: int | None,
        requester_username: str | None,
        requester_role: str,
    ) -> GeneratedReport:
        """Generate and persist one fraud-case report synchronously."""

        fraud_case = self.db.get(FraudCaseReview, case_id)
        if fraud_case is None:
            raise ReportCaseNotFoundError(
                f"Fraud case {case_id} was not found."
            )

        report_type = self._value(request.report_type)
        export_format = self._value(request.export_format)
        title = request.title or self._default_title(
            case_id=case_id,
            report_type=report_type,
        )
        report = GeneratedReport(
            case_id=case_id,
            report_type=report_type,
            export_format=export_format,
            status=ReportStatus.PENDING.value,
            title=title,
            generated_by_user_id=requester_user_id,
            generated_by_username=requester_username,
        )
        self.db.add(report)
        self.db.flush()

        try:
            report.status = ReportStatus.PROCESSING.value
            report.started_at = datetime.now(timezone.utc)
            self.db.flush()

            options = ReportGenerationOptions(
                include_sensitive_data=request.include_sensitive_data,
                include_internal_comments=request.include_internal_comments,
                include_audit_logs=request.include_audit_logs,
            )
            payload = self.data_service.build_report_data(
                case_id=case_id,
                report_type=report_type,
                options=options,
                requester_role=requester_role,
                requester_user_id=requester_user_id,
                requester_username=requester_username,
            )
            exported = self.export_service.export(
                report_id=report.id,
                case_id=case_id,
                report_type=report_type,
                export_format=export_format,
                title=title,
                data=payload,
            )

            report.status = ReportStatus.COMPLETED.value
            report.stored_filename = exported.stored_filename
            report.storage_path = exported.storage_path
            report.mime_type = exported.mime_type
            report.file_size_bytes = exported.file_size_bytes
            report.sha256_hash = exported.sha256_hash
            report.failure_message = None
            report.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(report)
            return report

        except Exception as exc:
            report_id = report.id
            started_at = report.started_at
            self.db.rollback()
            persisted_report = self.db.get(GeneratedReport, report_id)

            if persisted_report is None:
                persisted_report = GeneratedReport(
                    id=report_id,
                    case_id=case_id,
                    report_type=report_type,
                    export_format=export_format,
                    status=ReportStatus.FAILED.value,
                    title=title,
                    generated_by_user_id=requester_user_id,
                    generated_by_username=requester_username,
                    started_at=started_at,
                )
                self.db.add(persisted_report)

            persisted_report.status = ReportStatus.FAILED.value
            persisted_report.failure_message = self._safe_failure_message(exc)
            persisted_report.completed_at = None
            self.db.commit()
            raise

    def get_report(
        self,
        *,
        report_id: int,
        include_deleted: bool = False,
    ) -> GeneratedReport:
        """Return one generated-report record."""

        report = self.db.get(GeneratedReport, report_id)
        if report is None or (report.is_deleted and not include_deleted):
            raise GeneratedReportNotFoundError(
                f"Generated report {report_id} was not found."
            )
        return report

    def list_reports(
        self,
        *,
        case_id: int | None = None,
        query: ReportListQuery | None = None,
    ) -> GeneratedReportListResponse:
        """List generated reports with validated filters and pagination."""

        filters = query or ReportListQuery()
        statement = select(GeneratedReport)
        count_statement = select(func.count(GeneratedReport.id))
        conditions: list[Any] = []

        if case_id is not None:
            conditions.append(GeneratedReport.case_id == case_id)
        if filters.report_type is not None:
            conditions.append(
                GeneratedReport.report_type == self._value(filters.report_type)
            )
        if filters.export_format is not None:
            conditions.append(
                GeneratedReport.export_format
                == self._value(filters.export_format)
            )
        if filters.status is not None:
            conditions.append(
                GeneratedReport.status == self._value(filters.status)
            )
        if not filters.include_deleted:
            conditions.append(GeneratedReport.is_deleted.is_(False))

        if conditions:
            statement = statement.where(*conditions)
            count_statement = count_statement.where(*conditions)

        statement = (
            statement.order_by(
                GeneratedReport.created_at.desc(),
                GeneratedReport.id.desc(),
            )
            .offset(filters.offset)
            .limit(filters.limit)
        )
        reports = list(self.db.scalars(statement).all())
        total = int(self.db.scalar(count_statement) or 0)
        items = [
            GeneratedReportSummary.model_validate(report)
            for report in reports
        ]
        return GeneratedReportListResponse(
            items=items,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    def prepare_download(self, *, report_id: int) -> ReportDownloadMetadata:
        """Validate file integrity and register a successful download."""

        report = self.get_report(report_id=report_id)
        if report.status != ReportStatus.COMPLETED.value:
            raise GeneratedReportUnavailableError(
                "The report has not completed successfully."
            )

        required_metadata = (
            report.stored_filename,
            report.storage_path,
            report.mime_type,
            report.file_size_bytes,
            report.sha256_hash,
            report.completed_at,
        )
        if any(value is None for value in required_metadata):
            raise GeneratedReportUnavailableError(
                "The report metadata is incomplete."
            )

        exists, size_matches, hash_matches = self.export_service.verify_file(
            storage_path=report.storage_path,
            expected_size=report.file_size_bytes,
            expected_sha256=report.sha256_hash,
        )
        if not exists:
            raise GeneratedReportUnavailableError(
                "The generated report file is missing."
            )
        if not size_matches or not hash_matches:
            raise GeneratedReportUnavailableError(
                "The generated report failed its integrity check."
            )

        report.download_count += 1
        report.last_downloaded_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(report)

        return ReportDownloadMetadata(
            report_id=report.id,
            case_id=report.case_id,
            filename=report.stored_filename,
            storage_path=report.storage_path,
            mime_type=report.mime_type,
            file_size_bytes=report.file_size_bytes,
            sha256_hash=report.sha256_hash,
            generated_at=report.completed_at,
        )

    def verify_report_integrity(
        self,
        *,
        report_id: int,
    ) -> ReportFileIntegrityResponse:
        """Verify whether a report's stored file matches its metadata."""

        report = self.get_report(report_id=report_id, include_deleted=True)
        if (
            not report.storage_path
            or report.file_size_bytes is None
            or not report.sha256_hash
        ):
            return ReportFileIntegrityResponse(
                report_id=report.id,
                exists=False,
                size_matches=False,
                hash_matches=False,
                valid=False,
                checked_at=datetime.now(timezone.utc),
            )

        exists, size_matches, hash_matches = self.export_service.verify_file(
            storage_path=report.storage_path,
            expected_size=report.file_size_bytes,
            expected_sha256=report.sha256_hash,
        )
        return ReportFileIntegrityResponse(
            report_id=report.id,
            exists=exists,
            size_matches=size_matches,
            hash_matches=hash_matches,
            valid=exists and size_matches and hash_matches,
            checked_at=datetime.now(timezone.utc),
        )

    def soft_delete_report(
        self,
        *,
        report_id: int,
        requester_user_id: int | None,
        requester_username: str | None,
        requester_role: str,
        remove_file: bool = True,
    ) -> ReportDeleteResponse:
        """Soft delete a report and optionally remove the stored file."""

        if requester_role.strip().lower() not in REPORT_DELETE_ROLES:
            raise GeneratedReportPermissionError(
                "Only an administrator may delete generated reports."
            )
        report = self.get_report(report_id=report_id, include_deleted=True)
        if report.is_deleted:
            raise GeneratedReportUnavailableError(
                "The report has already been deleted."
            )

        deleted_at = datetime.now(timezone.utc)
        if remove_file and report.storage_path:
            self.export_service.delete_file(report.storage_path)

        report.is_deleted = True
        report.status = ReportStatus.DELETED.value
        report.deleted_by_user_id = requester_user_id
        report.deleted_by_username = requester_username
        report.deleted_at = deleted_at
        self.db.commit()
        self.db.refresh(report)

        return ReportDeleteResponse(
            report_id=report.id,
            case_id=report.case_id,
            deleted_at=deleted_at,
            deleted_by_user_id=requester_user_id,
            deleted_by_username=requester_username,
        )

    def restore_report(
        self,
        *,
        report_id: int,
        requester_role: str,
    ) -> GeneratedReport:
        """Restore metadata only when the report file remains valid."""

        if requester_role.strip().lower() != "admin":
            raise GeneratedReportPermissionError(
                "Only an administrator may restore generated reports."
            )
        report = self.get_report(report_id=report_id, include_deleted=True)
        if not report.is_deleted:
            return report

        integrity = self.verify_report_integrity(report_id=report.id)
        if not integrity.valid:
            raise GeneratedReportUnavailableError(
                "The report cannot be restored because its file is unavailable."
            )

        report.is_deleted = False
        report.status = ReportStatus.COMPLETED.value
        report.deleted_by_user_id = None
        report.deleted_by_username = None
        report.deleted_at = None
        self.db.commit()
        self.db.refresh(report)
        return report

    @staticmethod
    def to_response(report: GeneratedReport) -> GeneratedReportResponse:
        """Convert a SQLAlchemy record to its detailed response schema."""

        return GeneratedReportResponse.model_validate(report)

    @staticmethod
    def _default_title(*, case_id: int, report_type: str) -> str:
        readable_type = report_type.replace("_", " ").title()
        return f"{readable_type} — Fraud Case {case_id}"

    @staticmethod
    def _safe_failure_message(exc: Exception) -> str:
        if isinstance(exc, ReportExportError):
            message = str(exc)
        elif isinstance(exc, ReportingServiceError):
            message = str(exc)
        else:
            message = "Report generation failed due to an internal error."
        return " ".join(message.split())[:MAX_FAILURE_MESSAGE_LENGTH]

    @staticmethod
    def _value(value: Any) -> str:
        return str(getattr(value, "value", value))
