from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.session import Base


if TYPE_CHECKING:
    from backend.app.models.case_evidence import CaseEvidence
    from backend.app.models.user import User


class EvidenceAccessLog(Base):
    __tablename__ = "evidence_access_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("case_evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    evidence: Mapped["CaseEvidence"] = relationship(back_populates="access_logs")
    user: Mapped["User | None"] = relationship(foreign_keys=[user_id])

    __table_args__ = (
        Index(
            "ix_evidence_access_logs_evidence_created_at",
            "evidence_id",
            "created_at",
        ),
    )
