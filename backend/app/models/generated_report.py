"""Database model for generated fraud-case reports."""

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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.reporting import ReportStatus
from backend.app.db.session import Base


if TYPE_CHECKING:
    from backend.app.models.fraud_case import FraudCaseReview
    from backend.app.models.user import User


class GeneratedReport(Base):
    """
    Persistent metadata for a generated fraud-case report.

    The report file is stored outside PostgreSQL. The database retains the
    report's location, integrity hash, generation status, ownership metadata,
    download statistics and soft-deletion information.
    """

    __tablename__ = "generated_reports"

    __table_args__ = (
        Index(
            "ix_generated_reports_case_created",
            "case_id",
            "created_at",
        ),
        Index(
            "ix_generated_reports_case_type",
            "case_id",
            "report_type",
        ),
        Index(
            "ix_generated_reports_status_created",
            "status",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "fraud_case_reviews.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    export_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReportStatus.PENDING.value,
        server_default=text("'pending'"),
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    generated_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    generated_by_username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    stored_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    storage_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    file_size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    sha256_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    failure_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    download_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    last_downloaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        index=True,
    )

    deleted_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
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

    fraud_case: Mapped["FraudCaseReview"] = relationship(
        "FraudCaseReview",
        back_populates="generated_reports",
    )

    generated_by_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[generated_by_user_id],
    )

    deleted_by_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[deleted_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<GeneratedReport("
            f"id={self.id}, "
            f"case_id={self.case_id}, "
            f"report_type={self.report_type!r}, "
            f"export_format={self.export_format!r}, "
            f"status={self.status!r}"
            f")>"
        )
