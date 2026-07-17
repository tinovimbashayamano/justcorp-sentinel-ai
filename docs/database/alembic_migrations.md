# Alembic Database Migrations

## Objective

This document describes database schema versioning for JustCorp Sentinel AI.

## Purpose

SQLAlchemy `create_all()` creates missing tables but does not safely modify existing schemas. Alembic provides version-controlled, repeatable database migrations.

## Migration Location

Migration configuration is stored in:

- `alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/`

## Authoritative Schema Process

Database schema changes must follow this process:

```text
Modify SQLAlchemy model
    |
Generate Alembic revision
    |
Review generated migration
    |
Apply migration
    |
Run tests
    |
Commit migration
```

## Common Commands

### View Current Revision

```shell
python -m alembic current
```

### View Migration History

```shell
python -m alembic history
```

### Generate Migration

```shell
python -m alembic revision --autogenerate -m "Describe schema change"
```

### Upgrade

```shell
python -m alembic upgrade head
```

### Downgrade One Revision

```shell
python -m alembic downgrade -1
```

## Existing Database Baseline

The existing development database was stamped at the initial migration revision because its tables already matched the current SQLAlchemy models.

Stamping records the revision without executing table-creation statements.

## Clean Database Verification

The initial migration was tested against a separate clean PostgreSQL database by:

- Upgrading from an empty database to head.
- Confirming all application tables.
- Downgrading to base.
- Upgrading to head again.

## Security Rules

- Database credentials are loaded from environment configuration.
- Credentials are not stored in `alembic.ini`.
- `.env` is never committed.
- Generated migrations must be reviewed before execution.
- Production schema changes must not rely on `create_all()`.

## Current Application Tables

- `users`
- `refresh_tokens`
- `fraud_score_records`
- `fraud_case_reviews`
- `alembic_version`

## Conclusion

Alembic provides a reproducible migration history and prevents manual schema repair from becoming the normal deployment process.
