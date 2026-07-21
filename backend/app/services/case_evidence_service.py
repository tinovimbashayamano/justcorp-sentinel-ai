import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.evidence import EvidenceCategory, EvidenceEvent
from backend.app.core.storage import EVIDENCE_STORAGE_DIR
from backend.app.models.case_evidence import CaseEvidence
from backend.app.models.evidence_access_log import EvidenceAccessLog
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.user import User, UserRole
from backend.app.services.audit_service import create_audit_log, get_client_ip
from backend.app.services.case_history_service import create_case_history
from backend.app.services.file_validation import (
    HASH_CHUNK_SIZE,
    MAX_UPLOAD_SIZE_BYTES,
    FileValidationError,
    generate_uuid_filename,
    sanitize_filename,
    validate_extension,
    validate_file_size,
    validate_mime_type,
)


EVIDENCE_RESOURCE_TYPE = "case_evidence"


class EvidenceNotFoundError(ValueError):
    pass


class EvidencePermissionError(ValueError):
    pass


class EvidenceIntegrityError(ValueError):
    pass


def _get_case(db: Session, case_id: int) -> FraudCaseReview:
    fraud_case = db.get(FraudCaseReview, case_id)
    if fraud_case is None:
        raise EvidenceNotFoundError(f"Fraud case {case_id} not found.")
    return fraud_case


def _get_evidence(
    db: Session,
    *,
    case_id: int,
    evidence_id: int,
    include_deleted: bool = False,
) -> CaseEvidence:
    _get_case(db, case_id)
    query = db.query(CaseEvidence).filter(
        CaseEvidence.id == evidence_id,
        CaseEvidence.case_id == case_id,
    )
    if not include_deleted:
        query = query.filter(CaseEvidence.is_deleted.is_(False))
    evidence = query.first()
    if evidence is None:
        raise EvidenceNotFoundError("Case evidence not found.")
    return evidence


def _request_user_agent(request: Request | None) -> str | None:
    return request.headers.get("user-agent") if request else None


def create_evidence_access_log(
    db: Session,
    *,
    evidence: CaseEvidence,
    user: User,
    action: str,
    request: Request | None = None,
    commit: bool = True,
) -> EvidenceAccessLog:
    access_log = EvidenceAccessLog(
        evidence_id=evidence.id,
        user_id=user.id,
        username=user.username,
        action=action,
        ip_address=get_client_ip(request),
        user_agent=_request_user_agent(request),
    )
    db.add(access_log)
    if commit:
        db.commit()
        db.refresh(access_log)
    else:
        db.flush()
    return access_log


def _audit_access_denied(
    db: Session,
    *,
    actor: User,
    operation: str,
    case_id: int,
    evidence_id: int | None,
    request: Request | None,
) -> None:
    create_audit_log(
        db=db,
        action=AuditAction.CASE_EVIDENCE_ACCESS_DENIED,
        status=AuditStatus.DENIED,
        user=actor,
        resource_type=EVIDENCE_RESOURCE_TYPE,
        resource_id=evidence_id,
        request=request,
        details={"case_id": case_id, "operation": operation},
    )


def _require_role(
    db: Session,
    *,
    actor: User,
    allowed: tuple[UserRole, ...],
    operation: str,
    case_id: int,
    evidence_id: int | None = None,
    request: Request | None = None,
) -> None:
    if actor.role in allowed:
        return
    _audit_access_denied(
        db,
        actor=actor,
        operation=operation,
        case_id=case_id,
        evidence_id=evidence_id,
        request=request,
    )
    raise EvidencePermissionError(
        "You do not have permission to perform this evidence action."
    )


def _history_details(evidence: CaseEvidence) -> dict[str, str | int]:
    return {
        "evidence_id": evidence.id,
        "filename": evidence.original_filename,
        "category": evidence.category,
    }


def _write_upload(upload: UploadFile, destination: Path) -> tuple[int, str]:
    temporary_path = destination.with_suffix(destination.suffix + ".part")
    digest = hashlib.sha256()
    total = 0

    try:
        upload.file.seek(0)
        with temporary_path.open("xb") as output:
            while chunk := upload.file.read(HASH_CHUNK_SIZE):
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE_BYTES:
                    raise FileValidationError(
                        "The uploaded file exceeds the 20 MB limit."
                    )
                digest.update(chunk)
                output.write(chunk)
        validate_file_size(total)
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise

    return total, digest.hexdigest()


def upload_evidence(
    db: Session,
    *,
    case_id: int,
    upload: UploadFile,
    category: EvidenceCategory,
    description: str | None,
    actor: User,
    request: Request | None = None,
) -> CaseEvidence:
    _require_role(
        db,
        actor=actor,
        allowed=(UserRole.ADMIN, UserRole.FRAUD_ANALYST),
        operation="upload",
        case_id=case_id,
        request=request,
    )
    fraud_case = _get_case(db, case_id)
    original_filename = sanitize_filename(upload.filename or "")
    extension = validate_extension(original_filename)
    mime_type = validate_mime_type(upload.content_type, extension)
    validated_category = EvidenceCategory(category)
    cleaned_description = description.strip() if description else None
    if cleaned_description and len(cleaned_description) > 1000:
        raise FileValidationError("Description cannot exceed 1000 characters.")

    EVIDENCE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    stored_filename = generate_uuid_filename(original_filename)
    destination = EVIDENCE_STORAGE_DIR / stored_filename
    size, sha256_hash = _write_upload(upload, destination)
    evidence = CaseEvidence(
        case_id=case_id,
        uploader_user_id=actor.id,
        uploader_username=actor.username,
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=str(destination),
        mime_type=mime_type,
        category=validated_category.value,
        file_size_bytes=size,
        sha256_hash=sha256_hash,
        description=cleaned_description,
    )

    try:
        db.add(evidence)
        db.flush()
        create_evidence_access_log(
            db=db,
            evidence=evidence,
            user=actor,
            action="upload",
            request=request,
            commit=False,
        )
        create_audit_log(
            db=db,
            action=AuditAction.CASE_EVIDENCE_UPLOAD,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type=EVIDENCE_RESOURCE_TYPE,
            resource_id=evidence.id,
            request=request,
            details=_history_details(evidence),
            commit=False,
        )
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=EvidenceEvent.UPLOADED,
            details=_history_details(evidence),
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

    db.refresh(evidence)
    return evidence


def list_evidence(
    db: Session,
    *,
    case_id: int,
    actor: User,
    limit: int = 50,
    offset: int = 0,
    request: Request | None = None,
) -> tuple[list[CaseEvidence], int]:
    _require_role(
        db,
        actor=actor,
        allowed=(UserRole.ADMIN, UserRole.FRAUD_ANALYST, UserRole.AUDITOR),
        operation="list",
        case_id=case_id,
        request=request,
    )
    _get_case(db, case_id)
    query = db.query(CaseEvidence).filter(
        CaseEvidence.case_id == case_id,
        CaseEvidence.is_deleted.is_(False),
    )
    total = query.count()
    items = (
        query.order_by(CaseEvidence.created_at.asc(), CaseEvidence.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def get_evidence(
    db: Session,
    *,
    case_id: int,
    evidence_id: int,
    actor: User,
    request: Request | None = None,
) -> CaseEvidence:
    _require_role(
        db,
        actor=actor,
        allowed=(UserRole.ADMIN, UserRole.FRAUD_ANALYST, UserRole.AUDITOR),
        operation="read",
        case_id=case_id,
        evidence_id=evidence_id,
        request=request,
    )
    return _get_evidence(db, case_id=case_id, evidence_id=evidence_id)


def verify_sha256(evidence: CaseEvidence) -> bool:
    path = Path(evidence.storage_path)
    if not path.is_file():
        raise EvidenceIntegrityError("The evidence file is unavailable.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return hmac.compare_digest(digest.hexdigest(), evidence.sha256_hash)


def download_evidence(
    db: Session,
    *,
    case_id: int,
    evidence_id: int,
    actor: User,
    request: Request | None = None,
) -> CaseEvidence:
    evidence = get_evidence(
        db,
        case_id=case_id,
        evidence_id=evidence_id,
        actor=actor,
        request=request,
    )
    if not verify_sha256(evidence):
        raise EvidenceIntegrityError("Evidence integrity verification failed.")
    fraud_case = _get_case(db, case_id)
    try:
        create_evidence_access_log(
            db=db,
            evidence=evidence,
            user=actor,
            action="download",
            request=request,
            commit=False,
        )
        create_audit_log(
            db=db,
            action=AuditAction.CASE_EVIDENCE_DOWNLOAD,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type=EVIDENCE_RESOURCE_TYPE,
            resource_id=evidence.id,
            request=request,
            details=_history_details(evidence),
            commit=False,
        )
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=EvidenceEvent.DOWNLOADED,
            details=_history_details(evidence),
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return evidence


def delete_evidence(
    db: Session,
    *,
    case_id: int,
    evidence_id: int,
    actor: User,
    request: Request | None = None,
) -> CaseEvidence:
    _require_role(
        db,
        actor=actor,
        allowed=(UserRole.ADMIN, UserRole.FRAUD_ANALYST),
        operation="delete",
        case_id=case_id,
        evidence_id=evidence_id,
        request=request,
    )
    evidence = _get_evidence(db, case_id=case_id, evidence_id=evidence_id)
    if actor.role != UserRole.ADMIN and evidence.uploader_user_id != actor.id:
        _audit_access_denied(
            db,
            actor=actor,
            operation="delete",
            case_id=case_id,
            evidence_id=evidence_id,
            request=request,
        )
        raise EvidencePermissionError(
            "Fraud analysts may delete only evidence they uploaded."
        )
    fraud_case = _get_case(db, case_id)
    try:
        evidence.is_deleted = True
        evidence.deleted_by_user_id = actor.id
        evidence.deleted_by_username = actor.username
        evidence.deleted_at = datetime.now(timezone.utc)
        db.flush()
        create_evidence_access_log(
            db=db,
            evidence=evidence,
            user=actor,
            action="delete",
            request=request,
            commit=False,
        )
        create_audit_log(
            db=db,
            action=AuditAction.CASE_EVIDENCE_DELETE,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type=EVIDENCE_RESOURCE_TYPE,
            resource_id=evidence.id,
            request=request,
            details=_history_details(evidence),
            commit=False,
        )
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=EvidenceEvent.DELETED,
            details=_history_details(evidence),
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(evidence)
    return evidence
