from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.auth import UserCreateRequest


class AuthenticationError(ValueError):
    """Raised when supplied authentication credentials are invalid."""


class RegistrationConflictError(ValueError):
    """Raised when registration data conflicts with an existing user."""


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(
    db: Session,
    username: str,
) -> User | None:
    normalized_username = username.strip().lower()

    return (
        db.query(User)
        .filter(User.username == normalized_username)
        .first()
    )


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = email.strip().lower()

    return (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )


def get_user_by_identifier(
    db: Session,
    identifier: str,
) -> User | None:
    normalized_identifier = identifier.strip().lower()

    return (
        db.query(User)
        .filter(
            or_(
                User.username == normalized_identifier,
                User.email == normalized_identifier,
            )
        )
        .first()
    )


def register_user(
    db: Session,
    request: UserCreateRequest,
) -> User:
    if get_user_by_username(db, request.username) is not None:
        raise RegistrationConflictError(
            "A user with this username already exists."
        )

    if get_user_by_email(db, request.email) is not None:
        raise RegistrationConflictError(
            "A user with this email already exists."
        )

    user = User(
        username=request.username,
        email=str(request.email),
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
        role=UserRole.VIEWER,
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as error:
        db.rollback()
        raise RegistrationConflictError(
            "The username or email already exists."
        ) from error

    return user


def authenticate_user(
    db: Session,
    username_or_email: str,
    password: str,
) -> User:
    user = get_user_by_identifier(
        db=db,
        identifier=username_or_email,
    )

    if user is None:
        raise AuthenticationError(
            "Incorrect username, email, or password."
        )

    if not verify_password(password, user.hashed_password):
        raise AuthenticationError(
            "Incorrect username, email, or password."
        )

    if not user.is_active:
        raise AuthenticationError(
            "User account is inactive."
        )

    return user


def issue_access_token(user: User) -> str:
    return create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )
