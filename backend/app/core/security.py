from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from backend.app.core.config import settings


password_hash = PasswordHash.recommended()


class TokenValidationError(ValueError):
    """Raised when an access token cannot be validated."""


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password must not be empty.")

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    if not plain_password or not hashed_password:
        return False

    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)

    expiration = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(
            minutes=settings.access_token_expire_minutes,
        )
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expiration,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as error:
        raise TokenValidationError(
            "Access token is invalid or expired."
        ) from error

    if payload.get("type") != "access":
        raise TokenValidationError(
            "Token is not an access token."
        )

    subject = payload.get("sub")

    if not subject:
        raise TokenValidationError(
            "Token subject is missing."
        )

    return payload
