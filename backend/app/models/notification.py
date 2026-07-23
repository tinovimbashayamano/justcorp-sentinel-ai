"""Database model for user notifications and operational alerts."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.notifications import (
    DEFAULT_MAX_DELIVERY_ATTEMPTS,
    DEFAULT_NOTIFICATION_CHANNEL,
    DEFAULT_NOTIFICATION_PRIORITY,
    DEFAULT_NOTIFICATION_STATUS,
)
from backend.app.db.session import Base


if TYPE_CHECKING:
    from backend.app.models.user import User


def _user_model() -> type[User]:
    """Import User only when SQLAlchemy resolves notification relationships."""

    from backend.app.models.user import User

    return User


class Notification(Base):
    """Persistent notification addressed to one application user."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    recipient_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DEFAULT_NOTIFICATION_PRIORITY,
        server_default=DEFAULT_NOTIFICATION_PRIORITY,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DEFAULT_NOTIFICATION_CHANNEL,
        server_default=DEFAULT_NOTIFICATION_CHANNEL,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DEFAULT_NOTIFICATION_STATUS,
        server_default=DEFAULT_NOTIFICATION_STATUS,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    entity_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    deduplication_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    max_delivery_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_MAX_DELIVERY_ATTEMPTS,
        server_default=str(DEFAULT_MAX_DELIVERY_ATTEMPTS),
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    recipient: Mapped["User"] = relationship(
        _user_model,
        foreign_keys=[recipient_user_id],
        back_populates="notifications",
    )
    actor: Mapped["User | None"] = relationship(
        _user_model,
        foreign_keys=[actor_user_id],
    )
    deleted_by: Mapped["User | None"] = relationship(
        _user_model,
        foreign_keys=[deleted_by_user_id],
    )

    __table_args__ = (
        CheckConstraint(
            "delivery_attempts >= 0",
            name="ck_notifications_delivery_attempts_nonnegative",
        ),
        CheckConstraint(
            "max_delivery_attempts > 0",
            name="ck_notifications_max_delivery_attempts_positive",
        ),
        CheckConstraint(
            "entity_id IS NULL OR entity_id > 0",
            name="ck_notifications_entity_id_positive",
        ),
        CheckConstraint(
            "(is_read = false AND read_at IS NULL) "
            "OR (is_read = true AND read_at IS NOT NULL)",
            name="ck_notifications_read_state_consistent",
        ),
        UniqueConstraint(
            "recipient_user_id",
            "deduplication_key",
            name="uq_notifications_recipient_deduplication_key",
        ),
        Index(
            "ix_notifications_recipient_unread",
            "recipient_user_id",
            "is_read",
            "is_deleted",
            "created_at",
        ),
        Index(
            "ix_notifications_recipient_status",
            "recipient_user_id",
            "status",
            "created_at",
        ),
        Index(
            "ix_notifications_entity",
            "entity_type",
            "entity_id",
        ),
        Index(
            "ix_notifications_retry_queue",
            "status",
            "next_retry_at",
            "delivery_attempts",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id!r} "
            f"recipient_user_id={self.recipient_user_id!r} "
            f"type={self.notification_type!r} "
            f"status={self.status!r}>"
        )
