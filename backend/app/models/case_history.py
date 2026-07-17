from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class CaseHistory(Base):
    __tablename__ = "case_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    case_id: Mapped[int] = mapped_column(
        ForeignKey(
            "fraud_case_reviews.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    actor_username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_case_history_case_created",
            "case_id",
            "created_at",
        ),
    )
