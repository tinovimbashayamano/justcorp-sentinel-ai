from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.security import (
    TokenValidationError,
    decode_access_token,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import get_user_by_id


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


AccessToken = Annotated[
    str,
    Depends(oauth2_scheme),
]


def get_current_user(
    token: AccessToken,
    db: DatabaseSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)
    except (
        TokenValidationError,
        TypeError,
        ValueError,
    ) as error:
        raise credentials_exception from error

    user = get_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return current_user


CurrentUser = Annotated[
    User,
    Depends(get_current_active_user),
]
