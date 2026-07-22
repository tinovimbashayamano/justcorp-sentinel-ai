"""add generated reports

Revision ID: 3e66ccc6c4ec
Revises: 9e261a00f295
Create Date: 2026-07-22 11:32:15.530962
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "3e66ccc6c4ec"
down_revision: str | None = "9e261a00f295"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generated_reports",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "case_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "report_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "export_format",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "generated_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "generated_by_username",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "stored_filename",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "storage_path",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            "mime_type",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "file_size_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "sha256_hash",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "failure_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "download_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "last_downloaded_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "deleted_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "deleted_by_username",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["fraud_case_reviews.id"],
            name="fk_generated_reports_case_id_fraud_case_reviews",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["generated_by_user_id"],
            ["users.id"],
            name="fk_generated_reports_generated_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by_user_id"],
            ["users.id"],
            name="fk_generated_reports_deleted_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="generated_reports_pkey",
        ),
    )

    op.create_index(
        "ix_generated_reports_case_id",
        "generated_reports",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_report_type",
        "generated_reports",
        ["report_type"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_export_format",
        "generated_reports",
        ["export_format"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_status",
        "generated_reports",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_generated_by_user_id",
        "generated_reports",
        ["generated_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_created_at",
        "generated_reports",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_is_deleted",
        "generated_reports",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_case_created",
        "generated_reports",
        ["case_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_case_type",
        "generated_reports",
        ["case_id", "report_type"],
        unique=False,
    )
    op.create_index(
        "ix_generated_reports_status_created",
        "generated_reports",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_generated_reports_status_created",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_case_type",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_case_created",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_is_deleted",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_created_at",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_generated_by_user_id",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_status",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_export_format",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_report_type",
        table_name="generated_reports",
    )
    op.drop_index(
        "ix_generated_reports_case_id",
        table_name="generated_reports",
    )
    op.drop_table("generated_reports")
