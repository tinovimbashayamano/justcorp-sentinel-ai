"""Pydantic schemas for fraud-case report generation and management."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from backend.app.core.reporting import (
    DEFAULT_REPORT_LIST_LIMIT,
    MAX_FAILURE_MESSAGE_LENGTH,
    MAX_REPORT_LIST_LIMIT,
    MAX_REPORT_TITLE_LENGTH,
    MIN_REPORT_TITLE_LENGTH,
    REPORT_FORMATS,
    REPORT_STATUSES,
    REPORT_TYPES,
    ReportFormat,
    ReportStatus,
    ReportType,
    validate_report_type_format_combination,
)


ReportTitle = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=MIN_REPORT_TITLE_LENGTH,
        max_length=MAX_REPORT_TITLE_LENGTH,
    ),
]


class ReportSchemaBase(BaseModel):
    """Base configuration shared by reporting schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        extra="forbid",
    )


class ReportGenerationRequest(ReportSchemaBase):
    """Request body used to generate a fraud-case report."""

    report_type: ReportType = Field(
        ...,
        description="Type of report to generate.",
        examples=[ReportType.COMPLETE_CASE.value],
    )

    export_format: ReportFormat = Field(
        ...,
        description="File format used for the generated report.",
        examples=[ReportFormat.PDF.value],
    )

    title: ReportTitle | None = Field(
        default=None,
        description=(
            "Optional custom report title. A default title is generated when "
            "this value is omitted."
        ),
        examples=["Complete fraud investigation report"],
    )

    include_sensitive_data: bool = Field(
        default=False,
        description=(
            "Whether fields classified as sensitive may be included. The "
            "reporting service must still apply role-based access controls."
        ),
    )

    include_internal_comments: bool = Field(
        default=False,
        description=(
            "Whether internal case comments should be included. This is still "
            "subject to user permissions."
        ),
    )

    include_audit_logs: bool = Field(
        default=False,
        description=(
            "Whether detailed audit records should be included where the "
            "selected report type supports them."
        ),
    )

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        """Normalize whitespace and reject effectively empty titles."""

        if value is None:
            return None

        normalized = " ".join(value.split())

        if not normalized:
            return None

        if len(normalized) < MIN_REPORT_TITLE_LENGTH:
            raise ValueError(
                "Report title must contain at least "
                f"{MIN_REPORT_TITLE_LENGTH} characters."
            )

        if len(normalized) > MAX_REPORT_TITLE_LENGTH:
            raise ValueError(
                "Report title must not exceed "
                f"{MAX_REPORT_TITLE_LENGTH} characters."
            )

        return normalized

    @model_validator(mode="after")
    def validate_type_and_format(self) -> "ReportGenerationRequest":
        """Reject unsupported report-type and export-format combinations."""

        report_type = (
            self.report_type.value
            if isinstance(self.report_type, ReportType)
            else str(self.report_type)
        )

        export_format = (
            self.export_format.value
            if isinstance(self.export_format, ReportFormat)
            else str(self.export_format)
        )

        validate_report_type_format_combination(
            report_type=report_type,
            export_format=export_format,
        )

        return self


class ReportGenerationOptions(ReportSchemaBase):
    """Normalized report-generation options passed to services."""

    include_sensitive_data: bool = False
    include_internal_comments: bool = False
    include_audit_logs: bool = False


class GeneratedReportBase(ReportSchemaBase):
    """Common generated-report response fields."""

    id: int = Field(
        ...,
        ge=1,
        description="Generated-report database identifier.",
    )

    case_id: int = Field(
        ...,
        ge=1,
        description="Fraud case associated with the report.",
    )

    report_type: ReportType = Field(
        ...,
        description="Generated report type.",
    )

    export_format: ReportFormat = Field(
        ...,
        description="Generated file format.",
    )

    status: ReportStatus = Field(
        ...,
        description="Current generation lifecycle state.",
    )

    title: str | None = Field(
        default=None,
        max_length=MAX_REPORT_TITLE_LENGTH,
        description="Human-readable report title.",
    )

    generated_by_user_id: int | None = Field(
        default=None,
        ge=1,
        description="User who initiated report generation.",
    )

    generated_by_username: str | None = Field(
        default=None,
        max_length=100,
        description="Username captured when generation was requested.",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when the report record was created.",
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp when the report metadata was last updated.",
    )


class GeneratedReportResponse(GeneratedReportBase):
    """Detailed API representation of one generated report."""

    stored_filename: str | None = Field(
        default=None,
        max_length=255,
        description="Server-side generated filename.",
    )

    mime_type: str | None = Field(
        default=None,
        max_length=150,
        description="MIME type of the generated file.",
    )

    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Generated file size in bytes.",
    )

    sha256_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        description="SHA-256 integrity digest of the generated file.",
    )

    failure_message: str | None = Field(
        default=None,
        max_length=MAX_FAILURE_MESSAGE_LENGTH,
        description="Sanitized report-generation failure description.",
    )

    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when report processing started.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when generation finished successfully.",
    )

    download_count: int = Field(
        default=0,
        ge=0,
        description="Number of successful report downloads.",
    )

    last_downloaded_at: datetime | None = Field(
        default=None,
        description="Most recent successful download timestamp.",
    )

    is_deleted: bool = Field(
        default=False,
        description="Whether the report has been soft deleted.",
    )

    deleted_by_user_id: int | None = Field(
        default=None,
        ge=1,
        description="User who soft deleted the report.",
    )

    deleted_by_username: str | None = Field(
        default=None,
        max_length=100,
        description="Username captured when the report was deleted.",
    )

    deleted_at: datetime | None = Field(
        default=None,
        description="Soft-deletion timestamp.",
    )

    is_downloadable: bool = Field(
        default=False,
        description=(
            "Whether the report currently satisfies the metadata conditions "
            "required for downloading."
        ),
    )

    @model_validator(mode="after")
    def derive_downloadable_state(self) -> "GeneratedReportResponse":
        """Derive download availability from report metadata."""

        status_value = (
            self.status.value
            if isinstance(self.status, ReportStatus)
            else str(self.status)
        )

        self.is_downloadable = bool(
            status_value == ReportStatus.COMPLETED.value
            and not self.is_deleted
            and self.stored_filename
            and self.mime_type
            and self.file_size_bytes is not None
            and self.sha256_hash
        )

        return self


class GeneratedReportSummary(GeneratedReportBase):
    """Condensed generated-report representation for list responses."""

    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Generated file size in bytes.",
    )

    download_count: int = Field(
        default=0,
        ge=0,
        description="Number of successful downloads.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Successful completion timestamp.",
    )

    is_deleted: bool = Field(
        default=False,
        description="Whether the report has been soft deleted.",
    )


class GeneratedReportListResponse(ReportSchemaBase):
    """Paginated generated-report collection."""

    items: list[GeneratedReportSummary] = Field(
        default_factory=list,
        description="Generated reports in the current result page.",
    )

    total: int = Field(
        ...,
        ge=0,
        description="Total number of records matching the filters.",
    )

    limit: int = Field(
        default=DEFAULT_REPORT_LIST_LIMIT,
        ge=1,
        le=MAX_REPORT_LIST_LIMIT,
        description="Maximum number of records requested.",
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of matching records skipped.",
    )

    has_more: bool = Field(
        default=False,
        description="Whether additional matching records remain.",
    )

    @model_validator(mode="after")
    def derive_has_more(self) -> "GeneratedReportListResponse":
        """Calculate whether another page of records exists."""

        self.has_more = self.offset + len(self.items) < self.total
        return self


class ReportListQuery(ReportSchemaBase):
    """Validated filtering and pagination parameters for report listings."""

    report_type: ReportType | None = Field(
        default=None,
        description="Optional report-type filter.",
    )

    export_format: ReportFormat | None = Field(
        default=None,
        description="Optional export-format filter.",
    )

    status: ReportStatus | None = Field(
        default=None,
        description="Optional lifecycle-status filter.",
    )

    include_deleted: bool = Field(
        default=False,
        description="Whether soft-deleted reports should be returned.",
    )

    limit: int = Field(
        default=DEFAULT_REPORT_LIST_LIMIT,
        ge=1,
        le=MAX_REPORT_LIST_LIMIT,
        description="Maximum records to return.",
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip.",
    )


class ReportDownloadMetadata(ReportSchemaBase):
    """Metadata required to stream a generated report securely."""

    report_id: int = Field(
        ...,
        ge=1,
        description="Generated-report identifier.",
    )

    case_id: int = Field(
        ...,
        ge=1,
        description="Associated fraud-case identifier.",
    )

    filename: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Filename presented to the client.",
    )

    storage_path: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Validated server-side report path.",
        exclude=True,
    )

    mime_type: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Report MIME type.",
    )

    file_size_bytes: int = Field(
        ...,
        ge=0,
        description="Expected report file size.",
    )

    sha256_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="Expected SHA-256 file digest.",
    )

    generated_at: datetime = Field(
        ...,
        description="Timestamp when the report was completed.",
    )

    @field_validator("sha256_hash")
    @classmethod
    def validate_sha256_hash(cls, value: str) -> str:
        """Validate that the digest is a lowercase hexadecimal SHA-256 value."""

        normalized = value.lower()

        if len(normalized) != 64:
            raise ValueError("SHA-256 hash must contain exactly 64 characters.")

        if any(character not in "0123456789abcdef" for character in normalized):
            raise ValueError("SHA-256 hash must be hexadecimal.")

        return normalized


class ReportGenerationAcceptedResponse(ReportSchemaBase):
    """Response returned when a report-generation request is accepted."""

    message: str = Field(
        default="Report generation accepted.",
        description="Human-readable request status.",
    )

    report: GeneratedReportResponse


class ReportDeleteResponse(ReportSchemaBase):
    """Response returned after a report is soft deleted."""

    message: str = Field(
        default="Report deleted successfully.",
        description="Human-readable deletion result.",
    )

    report_id: int = Field(
        ...,
        ge=1,
        description="Deleted generated-report identifier.",
    )

    case_id: int = Field(
        ...,
        ge=1,
        description="Associated fraud-case identifier.",
    )

    deleted_at: datetime = Field(
        ...,
        description="Soft-deletion timestamp.",
    )

    deleted_by_user_id: int | None = Field(
        default=None,
        ge=1,
        description="User who deleted the report.",
    )

    deleted_by_username: str | None = Field(
        default=None,
        max_length=100,
        description="Username captured at deletion time.",
    )


class ReportRestoreResponse(ReportSchemaBase):
    """Response returned when an administrator restores report metadata."""

    message: str = Field(
        default="Report restored successfully.",
        description="Human-readable restoration result.",
    )

    report: GeneratedReportResponse


class ReportFailureResponse(ReportSchemaBase):
    """Safe report-generation failure response."""

    report_id: int = Field(
        ...,
        ge=1,
        description="Generated-report identifier.",
    )

    status: ReportStatus = Field(
        default=ReportStatus.FAILED,
        description="Report lifecycle status.",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_FAILURE_MESSAGE_LENGTH,
        description="Sanitized failure description.",
    )

    failed_at: datetime = Field(
        ...,
        description="Timestamp when generation failed.",
    )


class ReportTypeCapabilities(ReportSchemaBase):
    """Supported export formats and options for one report type."""

    report_type: ReportType

    supported_formats: list[ReportFormat] = Field(
        default_factory=list,
        description="Export formats supported by this report type.",
    )

    supports_sensitive_data: bool = False
    supports_internal_comments: bool = False
    supports_audit_logs: bool = False


class ReportingCapabilitiesResponse(ReportSchemaBase):
    """API representation of all reporting capabilities."""

    report_types: list[ReportTypeCapabilities] = Field(
        default_factory=list,
    )

    available_report_types: list[str] = Field(
        default_factory=lambda: sorted(REPORT_TYPES),
    )

    available_formats: list[str] = Field(
        default_factory=lambda: sorted(REPORT_FORMATS),
    )

    available_statuses: list[str] = Field(
        default_factory=lambda: sorted(REPORT_STATUSES),
    )


class ReportFileIntegrityResponse(ReportSchemaBase):
    """Result of a generated-report integrity verification."""

    report_id: int = Field(..., ge=1)
    exists: bool
    size_matches: bool
    hash_matches: bool
    valid: bool
    checked_at: datetime


class ReportStatusUpdate(ReportSchemaBase):
    """Internal schema used when changing the generation lifecycle state."""

    status: ReportStatus

    failure_message: str | None = Field(
        default=None,
        max_length=MAX_FAILURE_MESSAGE_LENGTH,
    )

    stored_filename: str | None = Field(
        default=None,
        max_length=255,
    )

    storage_path: str | None = Field(
        default=None,
        max_length=1000,
    )

    mime_type: str | None = Field(
        default=None,
        max_length=150,
    )

    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
    )

    sha256_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )

    started_at: datetime | None = None
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_status_metadata(self) -> "ReportStatusUpdate":
        """Validate metadata required by terminal report states."""

        status_value = (
            self.status.value
            if isinstance(self.status, ReportStatus)
            else str(self.status)
        )

        if status_value == ReportStatus.COMPLETED.value:
            required_values = {
                "stored_filename": self.stored_filename,
                "storage_path": self.storage_path,
                "mime_type": self.mime_type,
                "file_size_bytes": self.file_size_bytes,
                "sha256_hash": self.sha256_hash,
                "completed_at": self.completed_at,
            }

            missing = [
                field_name
                for field_name, field_value in required_values.items()
                if field_value is None
            ]

            if missing:
                raise ValueError(
                    "Completed reports require the following metadata: "
                    + ", ".join(sorted(missing))
                )

            if self.failure_message is not None:
                raise ValueError(
                    "Completed reports cannot contain a failure message."
                )

        if status_value == ReportStatus.FAILED.value:
            if not self.failure_message:
                raise ValueError("Failed reports require a failure message.")

        return self
