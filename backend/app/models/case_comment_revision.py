from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class CaseCommentRevision(Base):
    __tablename__ = "case_comment_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    comment_id: Mapped[int] = mapped_column(
        ForeignKey("case_comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    editor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    editor_username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    previous_content: Mapped[str] = mapped_column(Text, nullable=False)

    previous_visibility: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_case_comment_revisions_comment_created_at",
            "comment_id",
            "created_at",
        ),
    )
