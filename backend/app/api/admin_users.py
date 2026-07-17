from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy.orm import Session

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.dependencies import AdminUser
from backend.app.db.session import get_db
from backend.app.schemas.auth import UserResponse
from backend.app.schemas.user_management import (
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
)
from backend.app.services.audit_service import safely_create_audit_log
from backend.app.services.user_management_service import (
    UserManagementError,
    get_user,
    list_users,
    update_user_role,
    update_user_status,
)


router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["Admin User Management"],
)


@router.get(
    "",
    response_model=list[UserResponse],
)
def read_users(
    _: AdminUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_users(
        db=db,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def read_user(
    user_id: int,
    _: AdminUser,
    db: Session = Depends(get_db),
):
    user = get_user(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )

    return user


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def change_user_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    request: Request,
    current_admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        target_user = get_user(db=db, user_id=user_id)
        old_role = (
            target_user.role.value
            if target_user is not None
            else None
        )

        updated_user = update_user_role(
            db=db,
            user_id=user_id,
            new_role=payload.role,
            current_admin=current_admin,
        )

        safely_create_audit_log(
            db=db,
            action=AuditAction.USER_ROLE_UPDATE,
            status=AuditStatus.SUCCESS,
            user=current_admin,
            resource_type="user",
            resource_id=updated_user.id,
            request=request,
            details={
                "old_role": old_role,
                "new_role": updated_user.role.value,
                "target_username": updated_user.username,
            },
        )

        return updated_user
    except UserManagementError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def change_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    request: Request,
    current_admin: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        target_user = get_user(db=db, user_id=user_id)
        old_status = (
            target_user.is_active
            if target_user is not None
            else None
        )

        updated_user = update_user_status(
            db=db,
            user_id=user_id,
            is_active=payload.is_active,
            current_admin=current_admin,
        )

        safely_create_audit_log(
            db=db,
            action=AuditAction.USER_STATUS_UPDATE,
            status=AuditStatus.SUCCESS,
            user=current_admin,
            resource_type="user",
            resource_id=updated_user.id,
            request=request,
            details={
                "old_is_active": old_status,
                "new_is_active": updated_user.is_active,
                "target_username": updated_user.username,
            },
        )

        return updated_user
    except UserManagementError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
