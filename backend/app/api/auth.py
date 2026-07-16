from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.auth import (
    AccessTokenResponse,
    UserCreateRequest,
    UserResponse,
)
from backend.app.services.auth_service import (
    AuthenticationError,
    RegistrationConflictError,
    authenticate_user,
    issue_access_token,
    register_user,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_auth_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        return register_user(
            db=db,
            request=request,
        )
    except RegistrationConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post(
    "/login",
    response_model=AccessTokenResponse,
)
def login_auth_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(
            db=db,
            username_or_email=form_data.username,
            password=form_data.password,
        )
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    access_token = issue_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_seconds": (
            settings.access_token_expire_minutes * 60
        ),
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: CurrentUser,
):
    return current_user
