"""Create initial application schema.

Revision ID: 0b30ce5fbdd8
Revises:
Create Date: 2026-07-17 12:09:45.048753
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision: str = "0b30ce5fbdd8"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the initial application tables and indexes."""
    op.create_table(
        "fraud_score_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.String(length=255), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("fraud_probability", sa.Float(), nullable=False),
        sa.Column("fraud_prediction", sa.Integer(), nullable=False),
        sa.Column("fraud_threshold", sa.Float(), nullable=False),
        sa.Column("risk_band", sa.String(length=30), nullable=False),
        sa.Column("feature_quality", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fraud_score_records_id"),
        "fraud_score_records",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fraud_score_records_transaction_id"),
        "fraud_score_records",
        ["transaction_id"],
        unique=False,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "fraud_analyst",
                "auditor",
                "viewer",
                name="user_role",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_email"),
        "users",
        ["email"],
        unique=True,
    )
    op.create_index(
        op.f("ix_users_id"),
        "users",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_users_username"),
        "users",
        ["username"],
        unique=True,
    )

    op.create_table(
        "fraud_case_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fraud_score_record_id", sa.Integer(), nullable=False),
        sa.Column("case_status", sa.String(length=50), nullable=False),
        sa.Column("analyst_decision", sa.String(length=100), nullable=True),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["fraud_score_record_id"],
            ["fraud_score_records.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fraud_case_reviews_fraud_score_record_id"),
        "fraud_case_reviews",
        ["fraud_score_record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fraud_case_reviews_id"),
        "fraud_case_reviews",
        ["id"],
        unique=False,
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column(
            "replaced_by_token_hash",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refresh_tokens_id"),
        "refresh_tokens",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_tokens_token_hash"),
        "refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"),
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the initial application tables in dependency order."""
    op.drop_index(
        op.f("ix_refresh_tokens_user_id"),
        table_name="refresh_tokens",
    )
    op.drop_index(
        op.f("ix_refresh_tokens_token_hash"),
        table_name="refresh_tokens",
    )
    op.drop_index(
        op.f("ix_refresh_tokens_id"),
        table_name="refresh_tokens",
    )
    op.drop_table("refresh_tokens")

    op.drop_index(
        op.f("ix_fraud_case_reviews_id"),
        table_name="fraud_case_reviews",
    )
    op.drop_index(
        op.f("ix_fraud_case_reviews_fraud_score_record_id"),
        table_name="fraud_case_reviews",
    )
    op.drop_table("fraud_case_reviews")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(
        op.f("ix_fraud_score_records_transaction_id"),
        table_name="fraud_score_records",
    )
    op.drop_index(
        op.f("ix_fraud_score_records_id"),
        table_name="fraud_score_records",
    )
    op.drop_table("fraud_score_records")
