"""Fraud-related domain events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from backend.app.events.base import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class HighRiskFraudDetected(DomainEvent):
    """Published when a transaction exceeds a high-risk threshold."""

    transaction_id: int
    fraud_score: float
    threshold: float
    transaction_amount: Decimal | None = None
    assigned_user_id: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FraudPredictionCompleted(DomainEvent):
    """Published when fraud scoring has completed."""

    transaction_id: int
    fraud_score: float
    is_fraud: bool
    requested_by_user_id: int | None = None
