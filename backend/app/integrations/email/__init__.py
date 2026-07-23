from backend.app.integrations.email.base import (
    EmailDeliveryError,
    EmailDeliveryResult,
    EmailMessage,
    EmailSender,
)
from backend.app.integrations.email.console_sender import (
    ConsoleEmailSender,
)
from backend.app.integrations.email.smtp_sender import (
    SMTPEmailSender,
    SMTPSettings,
)


__all__ = [
    "EmailDeliveryError",
    "EmailDeliveryResult",
    "EmailMessage",
    "EmailSender",
    "ConsoleEmailSender",
    "SMTPEmailSender",
    "SMTPSettings",
]
