"""Email provider contracts and data structures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class EmailDeliveryError(RuntimeError):
    """Raised when an email provider cannot deliver a message."""


@dataclass(frozen=True, slots=True)
class EmailMessage:
    """Provider-independent email message."""

    recipient: str
    subject: str
    body: str
    html_body: str | None = None
    sender: str | None = None
    reply_to: str | None = None
    cc: tuple[str, ...] = field(default_factory=tuple)
    bcc: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class EmailDeliveryResult:
    """Result returned by an email provider."""

    success: bool
    provider: str
    provider_message_id: str | None = None
    error_message: str | None = None


class EmailSender(ABC):
    """Base interface implemented by all email providers."""

    @abstractmethod
    def send(
        self,
        message: EmailMessage,
    ) -> EmailDeliveryResult:
        """Send an email message."""
