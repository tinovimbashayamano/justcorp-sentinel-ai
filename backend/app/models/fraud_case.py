from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


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
