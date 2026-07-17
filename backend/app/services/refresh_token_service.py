from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import (
    create_refresh_token,
    hash_refresh_token,
)
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User


class RefreshTokenError(ValueError):
    """Raised when a refresh token is invalid."""


def issue_refresh_token(
    db: Session,
    user: User,
) -> str:
    raw_token = create_refresh_token()
    token_hash = hash_refresh_token(raw_token)

    record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=(
            datetime.now(UTC)
            + timedelta(
                days=settings.refresh_token_expire_days
            )
        ),
        is_revoked=False,
    )

    db.add(record)
    db.commit()

    return raw_token


def get_refresh_token_record(
    db: Session,
    raw_token: str,
) -> RefreshToken | None:
    token_hash = hash_refresh_token(raw_token)

    return (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )


def validate_refresh_token(
    db: Session,
    raw_token: str,
) -> RefreshToken:
    record = get_refresh_token_record(
        db=db,
        raw_token=raw_token,
    )

    if record is None:
        raise RefreshTokenError(
            "Refresh token is invalid."
        )

    if record.is_revoked:
        raise RefreshTokenError(
            "Refresh token has been revoked."
        )

    expires_at = record.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= datetime.now(UTC):
        raise RefreshTokenError(
            "Refresh token has expired."
        )

    return record


def rotate_refresh_token(
    db: Session,
    current_record: RefreshToken,
    user: User,
) -> str:
    new_raw_token = create_refresh_token()
    new_token_hash = hash_refresh_token(new_raw_token)

    current_record.is_revoked = True
    current_record.revoked_at = datetime.now(UTC)
    current_record.replaced_by_token_hash = new_token_hash

    new_record = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=(
            datetime.now(UTC)
            + timedelta(
                days=settings.refresh_token_expire_days
            )
        ),
        is_revoked=False,
    )

    db.add(new_record)
    db.commit()

    return new_raw_token


def revoke_refresh_token(
    db: Session,
    raw_token: str,
) -> None:
    record = get_refresh_token_record(
        db=db,
        raw_token=raw_token,
    )

    if record is None:
        return

    if not record.is_revoked:
        record.is_revoked = True
        record.revoked_at = datetime.now(UTC)
        db.commit()
