from sqlalchemy import asc
from sqlalchemy.orm import Session

from backend.app.models.user import User, UserRole


class UserManagementError(ValueError):
    """Raised when a user-management operation is invalid."""


def list_users(
    db: Session,
    limit: int = 50,
    offset: int = 0,
) -> list[User]:
    return (
        db.query(User)
        .order_by(asc(User.id))
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_user(
    db: Session,
    user_id: int,
) -> User | None:
    return db.get(User, user_id)


def update_user_role(
    db: Session,
    user_id: int,
    new_role: UserRole,
    current_admin: User,
) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise UserManagementError(
            f"User {user_id} does not exist."
        )

    if user.id == current_admin.id and new_role != UserRole.ADMIN:
        raise UserManagementError(
            "Administrators cannot remove their own admin role."
        )

    user.role = new_role

    db.commit()
    db.refresh(user)

    return user


def update_user_status(
    db: Session,
    user_id: int,
    is_active: bool,
    current_admin: User,
) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise UserManagementError(
            f"User {user_id} does not exist."
        )

    if user.id == current_admin.id and not is_active:
        raise UserManagementError(
            "Administrators cannot deactivate their own account."
        )

    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return user
