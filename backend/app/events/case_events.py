"""Fraud-case and investigation domain events."""

from __future__ import annotations

from dataclasses import dataclass

from backend.app.events.base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class InvestigationAssigned(DomainEvent):
    """Published when a fraud case is assigned to an investigator."""

    case_id: int
    assigned_user_id: int
    assigned_by_user_id: int
    case_reference: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FraudCaseEscalated(DomainEvent):
    """Published when a fraud case is escalated."""

    case_id: int
    escalated_by_user_id: int
    recipient_user_ids: tuple[int, ...]
    escalation_reason: str
    case_reference: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FraudCaseStatusChanged(DomainEvent):
    """Published when the workflow status of a case changes."""

    case_id: int
    changed_by_user_id: int
    recipient_user_ids: tuple[int, ...]
    previous_status: str
    new_status: str
    case_reference: str | None = None
