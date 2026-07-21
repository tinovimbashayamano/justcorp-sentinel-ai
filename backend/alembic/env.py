from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.core.config import settings
from backend.app.db.session import Base

# Import every model so SQLAlchemy registers all tables.
from backend.app.models.audit_log import AuditLog
from backend.app.models.case_comment import CaseComment
from backend.app.models.case_comment_revision import CaseCommentRevision
from backend.app.models.case_history import CaseHistory
from backend.app.models.case_evidence import CaseEvidence
from backend.app.models.evidence_access_log import EvidenceAccessLog
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User


target_metadata = Base.metadata

# Alembic provides context.config while executing migration commands. Keeping
# it optional also allows target_metadata to be inspected via a direct import.
config = getattr(context, "config", None)

if config is not None:
    config.set_main_option(
        "sqlalchemy.url",
        settings.database_url,
    )

    if config.config_file_name is not None:
        fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    if config is None:
        raise RuntimeError("Alembic configuration is unavailable.")

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    if config is None:
        raise RuntimeError("Alembic configuration is unavailable.")

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if config is not None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
