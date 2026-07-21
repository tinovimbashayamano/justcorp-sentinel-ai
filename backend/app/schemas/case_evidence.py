from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.core.evidence import EvidenceCategory


class CaseEvidenceUploadRequest(BaseModel):
    category: EvidenceCategory = EvidenceCategory.OTHER
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CaseEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    uploader_user_id: int | None
    uploader_username: str
    original_filename: str
    stored_filename: str
    mime_type: str
    category: str
    file_size_bytes: int
    sha256_hash: str
    description: str | None
    is_deleted: bool
    deleted_by_user_id: int | None
    deleted_by_username: str | None
    deleted_at: datetime | None
    created_at: datetime


class CaseEvidenceListResponse(BaseModel):
    items: list[CaseEvidenceResponse]
    total: int
    limit: int
    offset: int


class EvidenceDownloadResponse(BaseModel):
    evidence_id: int
    filename: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str


class EvidenceDeletionResponse(BaseModel):
    id: int
    evidence_id: int
    case_id: int
    original_filename: str
    filename: str
    is_deleted: bool
    deleted_by_username: str | None
    deleted_at: datetime | None


# Concise aliases for callers that do not use the case-specific prefix.
EvidenceUploadRequest = CaseEvidenceUploadRequest
EvidenceResponse = CaseEvidenceResponse
EvidenceListResponse = CaseEvidenceListResponse
