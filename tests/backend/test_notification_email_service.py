"""Tests for notification email delivery."""

from backend.app.integrations.email.base import (
    EmailDeliveryResult,
    EmailMessage,
    EmailSender,
)
from backend.app.integrations.email.console_sender import (
    ConsoleEmailSender,
)
from backend.app.services.notification_email_service import (
    NotificationEmailService,
)


class FailingEmailSender(EmailSender):
    def send(
        self,
        message: EmailMessage,
    ) -> EmailDeliveryResult:
        return EmailDeliveryResult(
            success=False,
            provider="test",
            error_message="Email provider unavailable",
        )


def test_console_email_sender_returns_success():
    sender = ConsoleEmailSender()

    result = sender.send(
        EmailMessage(
            recipient="analyst@example.com",
            subject="Test email",
            body="Test body",
        )
    )

    assert result.success is True
    assert result.provider == "console"
    assert result.provider_message_id is not None


def test_email_notification_is_delivered(
    db_session,
    test_user,
):
    service = NotificationEmailService(
        db_session,
        email_sender=ConsoleEmailSender(),
        sender_email="notifications@justcorp.local",
    )

    notification = service.create_and_deliver_email_notification(
        recipient_user_id=test_user.id,
        title="Email delivery test",
        message="Email body",
        deduplication_key=f"email-success-{test_user.id}",
    )

    assert notification.channel == "email"
    assert notification.status == "delivered"
    assert notification.failure_reason is None
    assert notification.metadata_json["email_provider"] == "console"


def test_email_provider_failure_marks_notification_failed(
    db_session,
    test_user,
):
    service = NotificationEmailService(
        db_session,
        email_sender=FailingEmailSender(),
    )

    notification = service.create_and_deliver_email_notification(
        recipient_user_id=test_user.id,
        title="Failure test",
        message="This delivery should fail",
        deduplication_key=f"email-failure-{test_user.id}",
    )

    assert notification.status == "failed"
    assert notification.delivery_attempts == 1
    assert notification.failure_reason == "Email provider unavailable"
    assert notification.next_retry_at is not None
