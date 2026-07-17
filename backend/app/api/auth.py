from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.dependencies import CurrentUser
from backend.app.db.session import get_db
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    TokenPairResponse,
    UserCreateRequest,
    UserResponse,
)
from backend.app.services.auth_service import (
    AuthenticationError,
    RegistrationConflictError,
    authenticate_user,
    get_user_by_id,
    issue_access_token,
    register_user,
)
from backend.app.services.password_service import (
    PasswordChangeError,
    change_user_password,
)
from backend.app.services.refresh_token_service import (
    RefreshTokenError,
    issue_refresh_token,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    validate_refresh_token,
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
    response_model=TokenPairResponse,
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
    refresh_token = issue_refresh_token(
        db=db,
        user=user,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in_seconds": (
            settings.access_token_expire_minutes * 60
        ),
    }


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
)
def refresh_auth_tokens(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        token_record = validate_refresh_token(
            db=db,
            raw_token=request.refresh_token,
        )

        user = get_user_by_id(
            db=db,
            user_id=token_record.user_id,
        )

        if user is None or not user.is_active:
            raise RefreshTokenError(
                "Refresh token user is unavailable."
            )

        new_access_token = issue_access_token(user)

        new_refresh_token = rotate_refresh_token(
            db=db,
            current_record=token_record,
            user=user,
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in_seconds": (
                settings.access_token_expire_minutes * 60
            ),
        }

    except RefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout_auth_user(
    request: LogoutRequest,
    db: Session = Depends(get_db),
):
    revoke_refresh_token(
        db=db,
        raw_token=request.refresh_token,
    )

    return {
        "message": "Logout successful."
    }


@router.post(
    "/change-password",
    response_model=MessageResponse,
)
def change_authenticated_user_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        revoked_session_count = change_user_password(
            db=db,
            user=current_user,
            current_password=request.current_password,
            new_password=request.new_password,
        )

        return {
            "message": (
                "Password changed successfully. "
                f"{revoked_session_count} refresh session(s) revoked."
            )
        }

    except PasswordChangeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post(
    "/logout-all",
    response_model=MessageResponse,
)
def logout_all_auth_sessions(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    revoked_session_count = revoke_all_user_refresh_tokens(
        db=db,
        user_id=current_user.id,
    )

    return {
        "message": (
            f"{revoked_session_count} refresh session(s) revoked."
        )
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: CurrentUser,
):
    return current_user
