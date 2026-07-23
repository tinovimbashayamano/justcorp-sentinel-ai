"""SMTP email provider implementation."""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage as StandardEmailMessage

from backend.app.integrations.email.base import (
    EmailDeliveryResult,
    EmailMessage,
    EmailSender,
)


@dataclass(frozen=True, slots=True)
class SMTPSettings:
    """SMTP connection settings."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None
    sender_email: str | None = None
    use_tls: bool = True
    use_ssl: bool = False
    timeout_seconds: int = 30


class SMTPEmailSender(EmailSender):
    """Sends email through an SMTP server."""

    def __init__(
        self,
        settings: SMTPSettings,
    ) -> None:
        self.settings = settings

    def send(
        self,
        message: EmailMessage,
    ) -> EmailDeliveryResult:
        sender = message.sender or self.settings.sender_email

        if not sender:
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                error_message="SMTP sender email is not configured.",
            )

        if not message.recipient.strip():
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                error_message="Recipient email address is empty.",
            )

        email = StandardEmailMessage()
        email["From"] = sender
        email["To"] = message.recipient
        email["Subject"] = message.subject

        if message.reply_to:
            email["Reply-To"] = message.reply_to

        if message.cc:
            email["Cc"] = ", ".join(message.cc)

        if message.bcc:
            email["Bcc"] = ", ".join(message.bcc)

        email.set_content(message.body)

        if message.html_body:
            email.add_alternative(
                message.html_body,
                subtype="html",
            )

        recipients = [
            message.recipient,
            *message.cc,
            *message.bcc,
        ]

        try:
            if self.settings.use_ssl:
                context = ssl.create_default_context()

                with smtplib.SMTP_SSL(
                    self.settings.host,
                    self.settings.port,
                    timeout=self.settings.timeout_seconds,
                    context=context,
                ) as smtp:
                    self._authenticate(smtp)
                    smtp.send_message(
                        email,
                        from_addr=sender,
                        to_addrs=recipients,
                    )
            else:
                with smtplib.SMTP(
                    self.settings.host,
                    self.settings.port,
                    timeout=self.settings.timeout_seconds,
                ) as smtp:
                    smtp.ehlo()

                    if self.settings.use_tls:
                        context = ssl.create_default_context()
                        smtp.starttls(context=context)
                        smtp.ehlo()

                    self._authenticate(smtp)
                    smtp.send_message(
                        email,
                        from_addr=sender,
                        to_addrs=recipients,
                    )

            return EmailDeliveryResult(
                success=True,
                provider="smtp",
            )

        except (
            OSError,
            smtplib.SMTPException,
        ) as exc:
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                error_message=str(exc),
            )

    def _authenticate(
        self,
        smtp: smtplib.SMTP,
    ) -> None:
        if self.settings.username and self.settings.password:
            smtp.login(
                self.settings.username,
                self.settings.password,
            )
