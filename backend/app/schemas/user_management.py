from pydantic import BaseModel

from backend.app.models.user import UserRole


class UserRoleUpdateRequest(BaseModel):
    role: UserRole


class UserStatusUpdateRequest(BaseModel):
    is_active: bool
