"""Add audit logs.

Revision ID: e7c902005872
Revises: 0b30ce5fbdd8
Create Date: 2026-07-17 13:05:54.121750
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "e7c902005872"
down_revision: str | Sequence[str] | None = "0b30ce5fbdd8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the audit log table and reporting indexes."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("actor_username", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_id", sa.String(length=100), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_logs_action"),
        "audit_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_action_created_at",
        "audit_logs",
        ["action", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_actor_username"),
        "audit_logs",
        ["actor_username"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_created_at"),
        "audit_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_resource_id"),
        "audit_logs",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_resource_type"),
        "audit_logs",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_status"),
        "audit_logs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_user_created_at",
        "audit_logs",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_user_id"),
        "audit_logs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the audit log table and its indexes."""
    op.drop_index(
        op.f("ix_audit_logs_user_id"),
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_user_created_at",
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_status"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_resource_type"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_resource_id"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_created_at"),
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_actor_username"),
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_action_created_at",
        table_name="audit_logs",
    )
    op.drop_index(
        op.f("ix_audit_logs_action"),
        table_name="audit_logs",
    )
    op.drop_table("audit_logs")
