"""Domain-event handlers that create user notifications."""

from __future__ import annotations

from decimal import Decimal

from backend.app.events.case_events import (
    FraudCaseEscalated,
    FraudCaseStatusChanged,
    InvestigationAssigned,
)
from backend.app.events.fraud_events import (
    FraudPredictionCompleted,
    HighRiskFraudDetected,
)
from backend.app.events.report_events import (
    ReportGenerationCompleted,
    ReportGenerationFailed,
)
from backend.app.services.notification_service import NotificationService


class NotificationDomainEventHandlers:
    """
    Converts domain events into persistent notifications.

    Event-specific information is stored in metadata so the implementation
    remains compatible with the current NotificationType enum.
    """

    def __init__(
        self,
        notification_service: NotificationService,
    ) -> None:
        self.notification_service = notification_service

    def handle_high_risk_fraud(
        self,
        event: HighRiskFraudDetected,
    ) -> None:
        if event.assigned_user_id is None:
            return

        amount_text = self._format_amount(event.transaction_amount)

        message = (
            f"Transaction {event.transaction_id} produced a fraud score of "
            f"{event.fraud_score:.2%}, exceeding the configured threshold of "
            f"{event.threshold:.2%}."
        )

        if amount_text:
            message += f" Transaction amount: {amount_text}."

        self.notification_service.create_notification(
            recipient_user_id=event.assigned_user_id,
            notification_type="system",
            priority="critical",
            channel="in_app",
            title="High-risk transaction detected",
            message=message,
            entity_type="transaction",
            entity_id=event.transaction_id,
            action_url=f"/transactions/{event.transaction_id}",
            metadata={
                "event_type": type(event).__name__,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "fraud_score": event.fraud_score,
                "threshold": event.threshold,
            },
            deduplication_key=(
                f"high-risk-fraud:{event.transaction_id}:"
                f"{event.assigned_user_id}"
            ),
        )

    def handle_prediction_completed(
        self,
        event: FraudPredictionCompleted,
    ) -> None:
        if event.requested_by_user_id is None:
            return

        classification = (
            "potentially fraudulent"
            if event.is_fraud
            else "not fraudulent"
        )

        self.notification_service.create_notification(
            recipient_user_id=event.requested_by_user_id,
            notification_type="system",
            priority="high" if event.is_fraud else "normal",
            channel="in_app",
            title="Fraud assessment completed",
            message=(
                f"Transaction {event.transaction_id} was classified as "
                f"{classification} with a score of "
                f"{event.fraud_score:.2%}."
            ),
            entity_type="transaction",
            entity_id=event.transaction_id,
            action_url=f"/transactions/{event.transaction_id}",
            metadata={
                "event_type": type(event).__name__,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "fraud_score": event.fraud_score,
                "is_fraud": event.is_fraud,
            },
            deduplication_key=(
                f"prediction-completed:{event.transaction_id}:"
                f"{event.requested_by_user_id}"
            ),
        )

    def handle_investigation_assigned(
        self,
        event: InvestigationAssigned,
    ) -> None:
        case_label = event.case_reference or str(event.case_id)

        self.notification_service.create_notification(
            recipient_user_id=event.assigned_user_id,
            actor_user_id=event.assigned_by_user_id,
            notification_type="system",
            priority="high",
            channel="in_app",
            title="Investigation assigned",
            message=(
                f"Fraud case {case_label} has been assigned to you for "
                "investigation."
            ),
            entity_type="fraud_case",
            entity_id=event.case_id,
            action_url=f"/cases/{event.case_id}",
            metadata={
                "event_type": type(event).__name__,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "assigned_by_user_id": event.assigned_by_user_id,
            },
            deduplication_key=(
                f"investigation-assigned:{event.case_id}:"
                f"{event.assigned_user_id}"
            ),
        )

    def handle_case_escalated(
        self,
        event: FraudCaseEscalated,
    ) -> None:
        case_label = event.case_reference or str(event.case_id)

        self.notification_service.create_bulk_notifications(
            recipient_user_ids=event.recipient_user_ids,
            actor_user_id=event.escalated_by_user_id,
            notification_type="system",
            priority="critical",
            channel="in_app",
            title="Fraud case escalated",
            message=(
                f"Fraud case {case_label} was escalated. Reason: "
                f"{event.escalation_reason}"
            ),
            entity_type="fraud_case",
            entity_id=event.case_id,
            action_url=f"/cases/{event.case_id}",
            metadata={
                "event_type": type(event).__name__,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "escalation_reason": event.escalation_reason,
            },
        )

    def handle_case_status_changed(
        self,
        event: FraudCaseStatusChanged,
    ) -> None:
        case_label = event.case_reference or str(event.case_id)

        self.notification_service.create_bulk_notifications(
            recipient_user_ids=event.recipient_user_ids,
            actor_user_id=event.changed_by_user_id,
            notification_type="system",
            priority="normal",
            channel="in_app",
            title="Fraud case status updated",
            message=(
                f"Fraud case {case_label} changed from "
                f"'{event.previous_status}' to '{event.new_status}'."
            ),
            entity_type="fraud_case",
            entity_id=event.case_id,
            action_url=f"/cases/{event.case_id}",
            metadata={
                "event_type": type(event).__name__,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "previous_status": event.previous_status,
                "new_status": event.new_status,
            },
        )

    def handle_report_completed(
        self,
        event: ReportGenerationCompleted,
    ) -> None:
        self.notification_service.create_notification(
            recipient_user_id=event.requested_by_user_id,
            notification_type="system",
            priority="normal",
            channel="in_app",
            title="Report ready",
            message=(
                f"The report '{event.report_name}' has been generated "
                "successfully."
            ),
            entity_type="report",
            entity_id=event.report_id,
            action_url=event.download_url or f"/reports/{event.report_id}",
            metadata={
                "event_type": type(event).__name__,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "case_id": event.case_id,
            },
            deduplication_key=(
                f"report-completed:{event.report_id}:"
                f"{event.requested_by_user_id}"
            ),
        )

    def handle_report_failed(
        self,
        event: ReportGenerationFailed,
    ) -> None:
        entity_id = event.report_id or event.case_id

        self.notification_service.create_notification(
            recipient_user_id=event.requested_by_user_id,
            notification_type="system",
            priority="high",
            channel="in_app",
            title="Report generation failed",
            message=(
                f"The report '{event.report_name}' could not be generated. "
                f"Reason: {event.failure_reason}"
            ),
            entity_type="report",
            entity_id=entity_id,
            metadata={
                "event_type": type(event).__name__,
                "event_id": event.event_id,
                "correlation_id": event.correlation_id,
                "case_id": event.case_id,
                "failure_reason": event.failure_reason,
            },
            deduplication_key=(
                f"report-failed:{event.report_id or 0}:"
                f"{event.requested_by_user_id}:"
                f"{event.event_id}"
            ),
        )

    @staticmethod
    def _format_amount(
        amount: Decimal | None,
    ) -> str | None:
        if amount is None:
            return None

        return f"{amount:,.2f}"
