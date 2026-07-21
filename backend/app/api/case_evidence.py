from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.dependencies import CurrentUser
from backend.app.core.evidence import EvidenceCategory
from backend.app.db.session import get_db
from backend.app.schemas.case_evidence import (
    CaseEvidenceListResponse,
    CaseEvidenceResponse,
    EvidenceDeletionResponse,
)
from backend.app.services.case_evidence_service import (
    EvidenceIntegrityError,
    EvidenceNotFoundError,
    EvidencePermissionError,
    delete_evidence,
    download_evidence,
    get_evidence,
    list_evidence,
    upload_evidence,
)
from backend.app.services.file_validation import FileValidationError


router = APIRouter(prefix="/api/v1/cases", tags=["Case Evidence"])


def _raise_evidence_error(error: ValueError) -> None:
    if isinstance(error, EvidenceNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, EvidencePermissionError):
        raise HTTPException(status_code=403, detail=str(error)) from error
    if isinstance(error, EvidenceIntegrityError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, FileValidationError):
        raise HTTPException(status_code=400, detail=str(error)) from error
    raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{case_id}/evidence", response_model=CaseEvidenceResponse)
def create_case_evidence(
    case_id: int,
    request: Request,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    category: EvidenceCategory = Form(EvidenceCategory.OTHER),
    description: str | None = Form(default=None, max_length=1000),
    db: Session = Depends(get_db),
):
    try:
        return upload_evidence(
            db,
            case_id=case_id,
            upload=file,
            category=category,
            description=description,
            actor=current_user,
            request=request,
        )
    except ValueError as error:
        _raise_evidence_error(error)


@router.get("/{case_id}/evidence", response_model=CaseEvidenceListResponse)
def read_case_evidence_list(
    case_id: int,
    request: Request,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        items, total = list_evidence(
            db,
            case_id=case_id,
            actor=current_user,
            limit=limit,
            offset=offset,
            request=request,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}
    except ValueError as error:
        _raise_evidence_error(error)


@router.get("/{case_id}/evidence/{evidence_id}", response_model=CaseEvidenceResponse)
def read_case_evidence(
    case_id: int,
    evidence_id: int,
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        return get_evidence(
            db,
            case_id=case_id,
            evidence_id=evidence_id,
            actor=current_user,
            request=request,
        )
    except ValueError as error:
        _raise_evidence_error(error)


@router.get("/{case_id}/evidence/{evidence_id}/download")
def download_case_evidence(
    case_id: int,
    evidence_id: int,
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        evidence = download_evidence(
            db,
            case_id=case_id,
            evidence_id=evidence_id,
            actor=current_user,
            request=request,
        )
        return FileResponse(
            path=Path(evidence.storage_path),
            media_type=evidence.mime_type,
            filename=evidence.original_filename,
            headers={"X-Content-SHA256": evidence.sha256_hash},
        )
    except ValueError as error:
        _raise_evidence_error(error)


@router.delete(
    "/{case_id}/evidence/{evidence_id}",
    response_model=EvidenceDeletionResponse,
)
def remove_case_evidence(
    case_id: int,
    evidence_id: int,
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    try:
        evidence = delete_evidence(
            db,
            case_id=case_id,
            evidence_id=evidence_id,
            actor=current_user,
            request=request,
        )
        return {
            "id": evidence.id,
            "evidence_id": evidence.id,
            "case_id": evidence.case_id,
            "original_filename": evidence.original_filename,
            "filename": evidence.original_filename,
            "is_deleted": evidence.is_deleted,
            "deleted_by_username": evidence.deleted_by_username,
            "deleted_at": evidence.deleted_at,
        }
    except ValueError as error:
        _raise_evidence_error(error)
