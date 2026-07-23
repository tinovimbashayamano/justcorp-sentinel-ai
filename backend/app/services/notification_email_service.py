"""Email delivery and retry processing for notifications."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.integrations.email.base import (
    EmailMessage,
    EmailSender,
)
from backend.app.models.notification import Notification
from backend.app.models.user import User
from backend.app.services.notification_service import (
    NotificationConflictError,
    NotificationService,
    NotificationValidationError,
)


@dataclass(frozen=True, slots=True)
class EmailProcessingSummary:
    """Summary returned after processing an email queue."""

    examined: int
    delivered: int
    failed: int
    skipped: int


class NotificationEmailService:
    """
    Delivers notifications whose channel is email.

    Delivery state remains controlled by NotificationService so this component
    does not duplicate lifecycle rules.
    """

    def __init__(
        self,
        db: Session,
        *,
        email_sender: EmailSender,
        notification_service: NotificationService | None = None,
        sender_email: str | None = None,
    ) -> None:
        self.db = db
        self.email_sender = email_sender
        self.notification_service = (
            notification_service or NotificationService(db)
        )
        self.sender_email = sender_email

    def deliver_notification(
        self,
        notification_id: int,
    ) -> Notification:
        notification = self.notification_service.get_notification(
            notification_id=notification_id,
        )

        if notification.channel != "email":
            raise NotificationValidationError(
                f"Notification {notification.id} is not an email notification."
            )

        if notification.status == "delivered":
            return notification

        if notification.status == "cancelled":
            raise NotificationConflictError(
                "A cancelled notification cannot be emailed."
            )

        recipient = self._get_recipient(notification.recipient_user_id)
        recipient_email = self._get_user_email(recipient)

        if not recipient_email:
            return self.notification_service.mark_failed(
                notification_id=notification.id,
                failure_reason=(
                    f"Recipient user {recipient.id} has no email address."
                ),
            )

        result = self.email_sender.send(
            EmailMessage(
                recipient=recipient_email,
                subject=notification.title,
                body=notification.message,
                sender=self.sender_email,
            )
        )

        if result.success:
            notification = self.notification_service.mark_delivered(
                notification_id=notification.id,
            )

            self._record_provider_metadata(
                notification,
                provider=result.provider,
                provider_message_id=result.provider_message_id,
            )

            return notification

        return self.notification_service.mark_failed(
            notification_id=notification.id,
            failure_reason=(
                result.error_message
                or f"{result.provider} email delivery failed."
            ),
        )

    def process_retry_queue(
        self,
        *,
        limit: int = 100,
    ) -> EmailProcessingSummary:
        if limit < 1 or limit > 500:
            raise NotificationValidationError(
                "Retry queue limit must be between 1 and 500."
            )

        retryable = [
            notification
            for notification in self.notification_service.get_retry_queue(
                limit=limit
            )
            if notification.channel == "email"
        ]

        delivered = 0
        failed = 0
        skipped = 0

        for notification in retryable:
            try:
                result = self.deliver_notification(notification.id)

                if result.status == "delivered":
                    delivered += 1
                elif result.status == "failed":
                    failed += 1
                else:
                    skipped += 1

            except NotificationConflictError:
                skipped += 1
            except Exception as exc:
                self.notification_service.mark_failed(
                    notification_id=notification.id,
                    failure_reason=f"Unexpected email error: {exc}",
                )
                failed += 1

        return EmailProcessingSummary(
            examined=len(retryable),
            delivered=delivered,
            failed=failed,
            skipped=skipped,
        )

    def create_and_deliver_email_notification(
        self,
        *,
        recipient_user_id: int,
        title: str,
        message: str,
        actor_user_id: int | None = None,
        priority: str = "normal",
        entity_type: str | None = None,
        entity_id: int | None = None,
        action_url: str | None = None,
        metadata: dict[str, object] | None = None,
        deduplication_key: str | None = None,
    ) -> Notification:
        notification = self.notification_service.create_notification(
            recipient_user_id=recipient_user_id,
            actor_user_id=actor_user_id,
            notification_type="system",
            priority=priority,
            channel="email",
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            metadata=metadata,
            deduplication_key=deduplication_key,
            auto_deliver_in_app=False,
        )

        return self.deliver_notification(notification.id)

    def _get_recipient(
        self,
        user_id: int,
    ) -> User:
        user = self.db.scalar(select(User).where(User.id == user_id))

        if user is None:
            raise NotificationValidationError(
                f"Recipient user {user_id} does not exist."
            )

        return user

    @staticmethod
    def _get_user_email(
        user: User,
    ) -> str | None:
        email = getattr(user, "email", None)

        if email is None:
            return None

        normalized = str(email).strip()
        return normalized or None

    def _record_provider_metadata(
        self,
        notification: Notification,
        *,
        provider: str,
        provider_message_id: str | None,
    ) -> None:
        existing_metadata = dict(notification.metadata_json or {})

        existing_metadata["email_provider"] = provider

        if provider_message_id:
            existing_metadata["provider_message_id"] = provider_message_id

        notification.metadata_json = existing_metadata
        self.db.commit()
        self.db.refresh(notification)
