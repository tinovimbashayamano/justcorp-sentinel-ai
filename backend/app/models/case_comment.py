from datetime import datetime

from sqlalchemy import (
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


class CaseComment(Base):
    __tablename__ = "case_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    case_id: Mapped[int] = mapped_column(
        ForeignKey("fraud_case_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    author_username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    visibility: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="internal",
        server_default="internal",
        index=True,
    )

    is_edited: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    deleted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
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
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case = relationship(
        "FraudCaseReview",
        back_populates="comments",
        foreign_keys=[case_id],
    )
    author = relationship("User", foreign_keys=[author_user_id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by_user_id])

    __table_args__ = (
        Index("ix_case_comments_case_created_at", "case_id", "created_at"),
        Index("ix_case_comments_case_visibility", "case_id", "visibility"),
        Index("ix_case_comments_case_deleted", "case_id", "is_deleted"),
    )
