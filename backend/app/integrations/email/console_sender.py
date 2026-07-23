"""Development email provider that logs messages."""

from __future__ import annotations

import logging
from uuid import uuid4

from backend.app.integrations.email.base import (
    EmailDeliveryResult,
    EmailMessage,
    EmailSender,
)


logger = logging.getLogger(__name__)


class ConsoleEmailSender(EmailSender):
    """Email sender for local development and automated tests."""

    def send(
        self,
        message: EmailMessage,
    ) -> EmailDeliveryResult:
        if not message.recipient.strip():
            return EmailDeliveryResult(
                success=False,
                provider="console",
                error_message="Recipient email address is empty.",
            )

        provider_message_id = f"console-{uuid4()}"

        logger.info(
            "EMAIL DELIVERY\n"
            "Provider: console\n"
            "Message ID: %s\n"
            "From: %s\n"
            "To: %s\n"
            "CC: %s\n"
            "BCC: %s\n"
            "Subject: %s\n"
            "Body:\n%s",
            provider_message_id,
            message.sender or "not-configured",
            message.recipient,
            ", ".join(message.cc),
            ", ".join(message.bcc),
            message.subject,
            message.body,
        )

        return EmailDeliveryResult(
            success=True,
            provider="console",
            provider_message_id=provider_message_id,
        )
