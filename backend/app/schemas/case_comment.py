from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.core.case_comments import CommentVisibility


class CaseCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    visibility: CommentVisibility = CommentVisibility.INTERNAL

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Comment content cannot be empty.")

        return cleaned


class CaseCommentUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    visibility: CommentVisibility | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Comment content cannot be empty.")

        return cleaned


class CaseCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    author_user_id: int | None
    author_username: str
    content: str
    visibility: str
    is_edited: bool
    is_deleted: bool
    deleted_by_username: str | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CaseCommentListResponse(BaseModel):
    items: list[CaseCommentResponse]
    total: int
    limit: int
    offset: int


class CaseCommentRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comment_id: int
    editor_user_id: int | None
    editor_username: str
    previous_content: str
    previous_visibility: str
    created_at: datetime
