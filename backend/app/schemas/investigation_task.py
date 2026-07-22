from __future__ import annotations

from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from backend.app.core.investigation_tasks import (
    InvestigationTaskPriority,
    InvestigationTaskStatus,
)


def _normalize_optional_text(value: str | None) -> str | None:
    """Trim optional text and convert blank strings to None."""

    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    return normalized


class InvestigationTaskCreate(BaseModel):
    """Payload used to create a fraud investigation task."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Short task title.",
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Detailed task instructions.",
    )

    priority: InvestigationTaskPriority = Field(
        default=InvestigationTaskPriority.MEDIUM,
        description="Task priority.",
    )

    due_at: datetime | None = Field(
        default=None,
        description="Optional timezone-aware task deadline.",
    )

    assigned_to_user_id: int | None = Field(
        default=None,
        ge=1,
        description="Optional analyst user ID.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 3:
            raise ValueError("Task title must contain at least 3 characters.")

        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("due_at must include timezone information.")

        normalized = value.astimezone(timezone.utc)

        if normalized <= datetime.now(timezone.utc):
            raise ValueError("due_at must be in the future.")

        return normalized


class InvestigationTaskUpdate(BaseModel):
    """Payload used to update editable task details."""

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    priority: InvestigationTaskPriority | None = None

    due_at: datetime | None = None

    clear_description: bool = Field(
        default=False,
        description="Remove the existing description.",
    )

    clear_due_at: bool = Field(
        default=False,
        description="Remove the existing due date.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if len(normalized) < 3:
            raise ValueError("Task title must contain at least 3 characters.")

        return normalized

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("due_at must include timezone information.")

        normalized = value.astimezone(timezone.utc)

        if normalized <= datetime.now(timezone.utc):
            raise ValueError("due_at must be in the future.")

        return normalized

    @model_validator(mode="after")
    def validate_update_payload(self) -> InvestigationTaskUpdate:
        if self.clear_description and self.description is not None:
            raise ValueError(
                "description cannot be supplied when clear_description is true."
            )

        if self.clear_due_at and self.due_at is not None:
            raise ValueError(
                "due_at cannot be supplied when clear_due_at is true."
            )

        has_change = any(
            (
                self.title is not None,
                self.description is not None,
                self.priority is not None,
                self.due_at is not None,
                self.clear_description,
                self.clear_due_at,
            )
        )

        if not has_change:
            raise ValueError("At least one task field must be updated.")

        return self


class InvestigationTaskAssignment(BaseModel):
    """Payload used to assign, reassign, or unassign a task."""

    assigned_to_user_id: int | None = Field(
        default=None,
        ge=1,
        description="Target analyst user ID. Use null to unassign the task.",
    )

    reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional assignment or unassignment reason.",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)


class InvestigationTaskStatusUpdate(BaseModel):
    """Payload used for ordinary workflow status transitions."""

    status: InvestigationTaskStatus

    reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional explanation for the status change.",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str | None) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def validate_status_action(self) -> InvestigationTaskStatusUpdate:
        if self.status in {
            InvestigationTaskStatus.COMPLETED,
            InvestigationTaskStatus.CANCELLED,
        }:
            raise ValueError(
                "Use the dedicated completion or cancellation endpoint "
                "for terminal task statuses."
            )

        return self


class InvestigationTaskCompletion(BaseModel):
    """Payload used to complete an investigation task."""

    completion_note: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Summary of work performed and outcome.",
    )

    @field_validator("completion_note")
    @classmethod
    def validate_completion_note(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 3:
            raise ValueError(
                "completion_note must contain at least 3 characters."
            )

        return normalized


class InvestigationTaskCancellation(BaseModel):
    """Payload used to cancel an investigation task."""

    cancellation_reason: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Reason the task is no longer required.",
    )

    @field_validator("cancellation_reason")
    @classmethod
    def validate_cancellation_reason(cls, value: str) -> str:
        normalized = value.strip()

        if len(normalized) < 3:
            raise ValueError(
                "cancellation_reason must contain at least 3 characters."
            )

        return normalized


class InvestigationTaskResponse(BaseModel):
    """Public API representation of an investigation task."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int

    title: str
    description: str | None

    status: InvestigationTaskStatus
    priority: InvestigationTaskPriority
    due_at: datetime | None

    created_by_user_id: int | None
    created_by_username: str

    assigned_to_user_id: int | None
    assigned_to_username: str | None

    completed_by_user_id: int | None
    completed_by_username: str | None
    completed_at: datetime | None
    completion_note: str | None

    cancelled_by_user_id: int | None
    cancelled_by_username: str | None
    cancelled_at: datetime | None
    cancellation_reason: str | None

    is_deleted: bool
    deleted_by_user_id: int | None
    deleted_by_username: str | None
    deleted_at: datetime | None

    created_at: datetime
    updated_at: datetime

    is_overdue: bool = False


class InvestigationTaskListResponse(BaseModel):
    """Paginated task collection."""

    items: list[InvestigationTaskResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class InvestigationTaskDeleteResponse(BaseModel):
    """Response returned after soft deletion."""

    id: int
    task_id: int
    case_id: int
    title: str
    is_deleted: bool
    deleted_by_username: str
    deleted_at: datetime
