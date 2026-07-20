"""Add fraud case assignment.

Revision ID: 3b7d8e9f1a2c
Revises: e426cbf512ff
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "3b7d8e9f1a2c"
down_revision: str | Sequence[str] | None = "e426cbf512ff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "fraud_case_reviews",
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_fraud_case_reviews_assigned_to_user_id_users",
        "fraud_case_reviews",
        "users",
        ["assigned_to_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_fraud_case_reviews_assigned_to_user_id"),
        "fraud_case_reviews",
        ["assigned_to_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_fraud_case_reviews_assignee_status",
        "fraud_case_reviews",
        ["assigned_to_user_id", "case_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fraud_case_reviews_assignee_status",
        table_name="fraud_case_reviews",
    )
    op.drop_index(
        op.f("ix_fraud_case_reviews_assigned_to_user_id"),
        table_name="fraud_case_reviews",
    )
    op.drop_constraint(
        "fk_fraud_case_reviews_assigned_to_user_id_users",
        "fraud_case_reviews",
        type_="foreignkey",
    )
    op.drop_column("fraud_case_reviews", "assigned_to_user_id")
