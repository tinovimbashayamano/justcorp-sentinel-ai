from sqlalchemy.orm import Session

from backend.app.core.security import (
    hash_password,
    verify_password,
)
from backend.app.models.user import User
from backend.app.services.refresh_token_service import (
    revoke_all_user_refresh_tokens,
)


class PasswordChangeError(ValueError):
    """Raised when a password change cannot be completed."""


def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> int:
    if not verify_password(
        current_password,
        user.hashed_password,
    ):
        raise PasswordChangeError(
            "Current password is incorrect."
        )

    if verify_password(
        new_password,
        user.hashed_password,
    ):
        raise PasswordChangeError(
            "New password must be different from the current password."
        )

    user.hashed_password = hash_password(new_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    revoked_session_count = revoke_all_user_refresh_tokens(
        db=db,
        user_id=user.id,
    )

    return revoked_session_count
