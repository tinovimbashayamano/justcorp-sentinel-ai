"""Reporting domain events."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.events.base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ReportGenerationCompleted(DomainEvent):
    """Published after a report has been successfully generated."""

    report_id: int
    requested_by_user_id: int
    report_name: str
    download_url: str | None = None
    case_id: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReportGenerationFailed(DomainEvent):
    """Published when report generation fails."""

    requested_by_user_id: int
    report_name: str
    failure_reason: str
    report_id: int | None = None
    case_id: int | None = None
