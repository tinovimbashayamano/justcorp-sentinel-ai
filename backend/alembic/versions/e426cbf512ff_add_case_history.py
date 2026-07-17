"""Add case history.

Revision ID: e426cbf512ff
Revises: e7c902005872
Create Date: 2026-07-17 14:26:50.834692
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "e426cbf512ff"
down_revision: str | Sequence[str] | None = "e7c902005872"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add case workflow fields and chronological history storage."""
    op.add_column(
        "fraud_case_reviews",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="medium",
        ),
    )
    op.alter_column(
        "fraud_case_reviews",
        "priority",
        server_default=None,
    )
    op.add_column(
        "fraud_case_reviews",
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "fraud_case_reviews",
        sa.Column("closure_reason", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "case_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_username", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["fraud_case_reviews.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_case_history_case_created",
        "case_history",
        ["case_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_history_case_id"),
        "case_history",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_history_created_at"),
        "case_history",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_history_event_type"),
        "case_history",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_history_user_id"),
        "case_history",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove case history and the extended workflow fields."""
    op.drop_index(
        op.f("ix_case_history_user_id"),
        table_name="case_history",
    )
    op.drop_index(
        op.f("ix_case_history_event_type"),
        table_name="case_history",
    )
    op.drop_index(
        op.f("ix_case_history_created_at"),
        table_name="case_history",
    )
    op.drop_index(
        op.f("ix_case_history_case_id"),
        table_name="case_history",
    )
    op.drop_index(
        "ix_case_history_case_created",
        table_name="case_history",
    )
    op.drop_table("case_history")

    op.drop_column("fraud_case_reviews", "closure_reason")
    op.drop_column("fraud_case_reviews", "assigned_to")
    op.drop_column("fraud_case_reviews", "priority")
