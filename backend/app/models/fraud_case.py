from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.session import Base
from backend.app.models.user import User


if TYPE_CHECKING:
    from backend.app.models.case_comment import CaseComment


class FraudCaseReview(Base):
    __tablename__ = "fraud_case_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    fraud_score_record_id: Mapped[int] = mapped_column(
        ForeignKey("fraud_score_records.id"),
        nullable=False,
        index=True,
    )

    case_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    assigned_to_user: Mapped[User | None] = relationship(
        foreign_keys=[assigned_to_user_id],
    )

    comments: Mapped[list["CaseComment"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    closure_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    analyst_decision: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    analyst_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_fraud_case_reviews_assignee_status",
            "assigned_to_user_id",
            "case_status",
        ),
    )

    @property
    def assigned_to_username(self) -> str | None:
        if self.assigned_to_user is None:
            return None

        return self.assigned_to_user.username
