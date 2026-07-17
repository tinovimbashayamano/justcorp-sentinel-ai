from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    user_id: int | None
    actor_username: str | None
    action: str
    status: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    user_agent: str | None
    details: dict[str, Any] | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditLogQuery(BaseModel):
    action: str | None = None
    status: str | None = None
    actor_username: str | None = None
    resource_type: str | None = None

    limit: int = Field(
        default=50,
        ge=1,
        le=200,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )
