"""Add fraud case evidence

Revision ID: c91e8f2a6d44
Revises: b556c590b845
Create Date: 2026-07-21 10:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c91e8f2a6d44"
down_revision: Union[str, Sequence[str], None] = "b556c590b845"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("uploader_user_id", sa.Integer(), nullable=True),
        sa.Column("uploader_username", sa.String(length=100), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("deleted_by_username", sa.String(length=100), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["fraud_case_reviews.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["uploader_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(
        "ix_case_evidence_case_created_at",
        "case_evidence",
        ["case_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_case_evidence_case_deleted",
        "case_evidence",
        ["case_id", "is_deleted"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_evidence_case_id"), "case_evidence", ["case_id"], unique=False
    )
    op.create_index(
        op.f("ix_case_evidence_category"),
        "case_evidence",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_evidence_created_at"),
        "case_evidence",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_evidence_is_deleted"),
        "case_evidence",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        op.f("ix_case_evidence_uploader_user_id"),
        "case_evidence",
        ["uploader_user_id"],
        unique=False,
    )

    op.create_table(
        "evidence_access_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["case_evidence.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evidence_access_logs_action"),
        "evidence_access_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_access_logs_created_at"),
        "evidence_access_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_evidence_access_logs_evidence_created_at",
        "evidence_access_logs",
        ["evidence_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_access_logs_evidence_id"),
        "evidence_access_logs",
        ["evidence_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_access_logs_user_id"),
        "evidence_access_logs",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_evidence_access_logs_user_id"),
        table_name="evidence_access_logs",
    )
    op.drop_index(
        op.f("ix_evidence_access_logs_evidence_id"),
        table_name="evidence_access_logs",
    )
    op.drop_index(
        "ix_evidence_access_logs_evidence_created_at",
        table_name="evidence_access_logs",
    )
    op.drop_index(
        op.f("ix_evidence_access_logs_created_at"),
        table_name="evidence_access_logs",
    )
    op.drop_index(
        op.f("ix_evidence_access_logs_action"),
        table_name="evidence_access_logs",
    )
    op.drop_table("evidence_access_logs")
    op.drop_index(op.f("ix_case_evidence_uploader_user_id"), table_name="case_evidence")
    op.drop_index(op.f("ix_case_evidence_is_deleted"), table_name="case_evidence")
    op.drop_index(op.f("ix_case_evidence_created_at"), table_name="case_evidence")
    op.drop_index(op.f("ix_case_evidence_category"), table_name="case_evidence")
    op.drop_index(op.f("ix_case_evidence_case_id"), table_name="case_evidence")
    op.drop_index("ix_case_evidence_case_deleted", table_name="case_evidence")
    op.drop_index("ix_case_evidence_case_created_at", table_name="case_evidence")
    op.drop_table("case_evidence")
