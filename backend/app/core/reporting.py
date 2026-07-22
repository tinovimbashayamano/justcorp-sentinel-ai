"""Constants and validation helpers for fraud-case reporting."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path


class ReportType(StrEnum):
    """Supported fraud-case report types."""

    CASE_SUMMARY = "case_summary"
    INVESTIGATION_TIMELINE = "investigation_timeline"
    TASK_SUMMARY = "task_summary"
    EVIDENCE_INVENTORY = "evidence_inventory"
    AUDIT_SUMMARY = "audit_summary"
    COMPLETE_CASE = "complete_case"


class ReportFormat(StrEnum):
    """Supported report export formats."""

    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class ReportStatus(StrEnum):
    """Lifecycle states for generated reports."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


REPORT_TYPES: frozenset[str] = frozenset(item.value for item in ReportType)

REPORT_FORMATS: frozenset[str] = frozenset(item.value for item in ReportFormat)

REPORT_STATUSES: frozenset[str] = frozenset(item.value for item in ReportStatus)


REPORT_READ_ROLES: frozenset[str] = frozenset(
    {
        "admin",
        "fraud_analyst",
        "auditor",
    }
)

REPORT_GENERATE_ROLES: frozenset[str] = frozenset(
    {
        "admin",
        "fraud_analyst",
        "auditor",
    }
)

REPORT_DELETE_ROLES: frozenset[str] = frozenset({"admin"})


MAX_REPORT_TITLE_LENGTH = 200
MIN_REPORT_TITLE_LENGTH = 3
MAX_FAILURE_MESSAGE_LENGTH = 1000

DEFAULT_REPORT_LIST_LIMIT = 50
MAX_REPORT_LIST_LIMIT = 100

REPORT_STORAGE_DIRECTORY = Path("storage") / "reports"


REPORT_MIME_TYPES: dict[str, str] = {
    ReportFormat.JSON.value: "application/json",
    ReportFormat.CSV.value: "text/csv; charset=utf-8",
    ReportFormat.PDF.value: "application/pdf",
}


REPORT_FILE_EXTENSIONS: dict[str, str] = {
    ReportFormat.JSON.value: ".json",
    ReportFormat.CSV.value: ".csv",
    ReportFormat.PDF.value: ".pdf",
}


CSV_SUPPORTED_REPORT_TYPES: frozenset[str] = frozenset(
    {
        ReportType.CASE_SUMMARY.value,
        ReportType.INVESTIGATION_TIMELINE.value,
        ReportType.TASK_SUMMARY.value,
        ReportType.EVIDENCE_INVENTORY.value,
        ReportType.AUDIT_SUMMARY.value,
    }
)


def validate_report_type_format_combination(
    report_type: str,
    export_format: str,
) -> None:
    """
    Validate that a report type can be exported in the requested format.

    Complete-case reports intentionally do not support CSV because the report
    contains several unrelated nested sections that cannot be represented
    reliably as one flat table.

    Raises:
        ValueError: When the requested combination is unsupported.
    """

    if report_type not in REPORT_TYPES:
        raise ValueError(f"Unsupported report type: {report_type}")

    if export_format not in REPORT_FORMATS:
        raise ValueError(f"Unsupported export format: {export_format}")

    if (
        export_format == ReportFormat.CSV.value
        and report_type not in CSV_SUPPORTED_REPORT_TYPES
    ):
        raise ValueError(
            f"Report type '{report_type}' cannot be exported as CSV."
        )


def ensure_report_storage_directory() -> Path:
    """
    Create and return the report-storage directory.

    The path is created lazily so importing application modules does not mutate
    the filesystem.
    """

    REPORT_STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    return REPORT_STORAGE_DIRECTORY
