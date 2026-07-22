from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.session import Base


if TYPE_CHECKING:
    from backend.app.models.fraud_case import FraudCaseReview
    from backend.app.models.user import User


class InvestigationTask(Base):
    """A controlled unit of investigation work attached to a fraud case."""

    __tablename__ = "investigation_tasks"

    __table_args__ = (
        Index(
            "ix_investigation_tasks_case_created_at",
            "case_id",
            "created_at",
        ),
        Index(
            "ix_investigation_tasks_case_status",
            "case_id",
            "status",
        ),
        Index(
            "ix_investigation_tasks_assignee_status",
            "assigned_to_user_id",
            "status",
        ),
        Index(
            "ix_investigation_tasks_due_status",
            "due_at",
            "status",
        ),
        Index(
            "ix_investigation_tasks_case_deleted",
            "case_id",
            "is_deleted",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    case_id: Mapped[int] = mapped_column(
        ForeignKey(
            "fraud_case_reviews.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        server_default="medium",
        index=True,
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_by_username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    assigned_to_username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    completed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    completed_by_username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completion_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cancelled_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    cancelled_by_username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    deleted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    deleted_by_username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    case: Mapped["FraudCaseReview"] = relationship(
        "FraudCaseReview",
        back_populates="investigation_tasks",
    )

    created_by_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )

    assigned_to_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
    )

    completed_by_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[completed_by_user_id],
    )

    cancelled_by_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[cancelled_by_user_id],
    )

    deleted_by_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[deleted_by_user_id],
    )
