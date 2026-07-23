"""Application event-handler registration."""

from __future__ import annotations

from backend.app.events.base import SynchronousEventBus
from backend.app.events.case_events import (
    FraudCaseEscalated,
    FraudCaseStatusChanged,
    InvestigationAssigned,
)
from backend.app.events.fraud_events import (
    FraudPredictionCompleted,
    HighRiskFraudDetected,
)
from backend.app.events.handlers.notification_handlers import (
    NotificationDomainEventHandlers,
)
from backend.app.events.report_events import (
    ReportGenerationCompleted,
    ReportGenerationFailed,
)


def register_notification_event_handlers(
    event_bus: SynchronousEventBus,
    handlers: NotificationDomainEventHandlers,
) -> None:
    """Register notification handlers with the application event bus."""

    event_bus.subscribe(
        HighRiskFraudDetected,
        handlers.handle_high_risk_fraud,
    )
    event_bus.subscribe(
        FraudPredictionCompleted,
        handlers.handle_prediction_completed,
    )
    event_bus.subscribe(
        InvestigationAssigned,
        handlers.handle_investigation_assigned,
    )
    event_bus.subscribe(
        FraudCaseEscalated,
        handlers.handle_case_escalated,
    )
    event_bus.subscribe(
        FraudCaseStatusChanged,
        handlers.handle_case_status_changed,
    )
    event_bus.subscribe(
        ReportGenerationCompleted,
        handlers.handle_report_completed,
    )
    event_bus.subscribe(
        ReportGenerationFailed,
        handlers.handle_report_failed,
    )
