import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.evidence import EvidenceEvent
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.case_evidence import CaseEvidence
from backend.app.models.case_history import CaseHistory
from backend.app.models.evidence_access_log import EvidenceAccessLog
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User, UserRole
from backend.app.services.file_validation import (
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
    FileValidationError,
    compute_sha256,
    generate_uuid_filename,
    sanitize_filename,
    validate_extension,
    validate_file_size,
    validate_mime_type,
)


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
client = TestClient(app)
PDF_BYTES = b"%PDF-1.7\njustcorp evidence\n%%EOF"
PNG_BYTES = b"\x89PNG\r\n\x1a\njustcorp evidence"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    monkeypatch.setattr(
        "backend.app.services.case_evidence_service.EVIDENCE_STORAGE_DIR",
        evidence_dir,
    )
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield evidence_dir
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def create_user(username: str, role: UserRole) -> User:
    with TestingSessionLocal() as db:
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password=hash_password("SecurePassword123!"),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user


def auth_headers(user: User, user_agent: str | None = None) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}
    if user_agent:
        headers["User-Agent"] = user_agent
    return headers


def create_case(label: str = "evidence-source") -> int:
    with TestingSessionLocal() as db:
        record = FraudScoreRecord(
            transaction_id=label,
            model_name="test-model",
            fraud_probability=0.9,
            fraud_prediction=1,
            fraud_threshold=0.84,
            risk_band="high",
            feature_quality={},
        )
        db.add(record)
        db.flush()
        case = FraudCaseReview(
            fraud_score_record_id=record.id,
            case_status="open",
            priority="medium",
            analyst_decision="pending",
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        return case.id


def upload(
    case_id: int,
    actor: User,
    *,
    filename: str = "report.pdf",
    content: bytes = PDF_BYTES,
    mime_type: str = "application/pdf",
    category: str = "bank_statement",
    description: str = "Customer bank statement",
):
    return client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": (filename, content, mime_type)},
        data={"category": category, "description": description},
        headers=auth_headers(actor),
    )


def evidence_url(case_id: int, evidence_id: int) -> str:
    return f"/api/v1/cases/{case_id}/evidence/{evidence_id}"


@pytest.mark.parametrize("extension", sorted(ALLOWED_EXTENSIONS))
def test_allowed_extensions(extension: str):
    assert validate_extension(f"evidence.{extension}") == extension


@pytest.mark.parametrize(
    ("extension", "mime_type"),
    [
        ("pdf", "application/pdf"),
        ("png", "image/png"),
        ("jpg", "image/jpeg"),
        ("jpeg", "image/jpeg"),
        ("csv", "text/csv"),
        ("txt", "text/plain"),
        ("json", "application/json"),
    ],
)
def test_allowed_mime_types(extension: str, mime_type: str):
    assert validate_mime_type(mime_type, extension) == mime_type


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("../../private/report.pdf", "report.pdf"),
        (r"C:\private\report.pdf", "report.pdf"),
        ("report<script>.pdf", "report_script_.pdf"),
    ],
)
def test_sanitize_filename(filename: str, expected: str):
    assert sanitize_filename(filename) == expected


@pytest.mark.parametrize(
    "operation",
    [
        lambda: validate_extension("payload.exe"),
        lambda: validate_mime_type("application/x-msdownload", "pdf"),
        lambda: validate_file_size(0),
        lambda: validate_file_size(MAX_UPLOAD_SIZE_BYTES + 1),
        lambda: sanitize_filename("   "),
    ],
)
def test_file_validation_rejections(operation):
    with pytest.raises(FileValidationError):
        operation()


def test_uuid_filename_is_unique_and_preserves_extension():
    first = generate_uuid_filename("report.pdf")
    second = generate_uuid_filename("report.pdf")
    assert first.endswith(".pdf") and first != second


@pytest.mark.parametrize("source_kind", ["bytes", "path", "stream"])
def test_compute_sha256(source_kind: str, tmp_path: Path):
    expected = hashlib.sha256(PDF_BYTES).hexdigest()
    if source_kind == "bytes":
        source = PDF_BYTES
    else:
        path = tmp_path / "hash.pdf"
        path.write_bytes(PDF_BYTES)
        source = path if source_kind == "path" else path.open("rb")
    try:
        assert compute_sha256(source) == expected
    finally:
        if source_kind == "stream":
            source.close()


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        (UserRole.ADMIN, 200),
        (UserRole.FRAUD_ANALYST, 200),
        (UserRole.AUDITOR, 403),
        (UserRole.VIEWER, 403),
    ],
)
def test_upload_rbac(role: UserRole, expected_status: int):
    actor = create_user(f"upload-{role.value}", role)
    assert upload(create_case(role.value), actor).status_code == expected_status


def test_upload_pdf_and_png():
    admin = create_user("formats-admin", UserRole.ADMIN)
    pdf = upload(create_case("pdf"), admin)
    png = upload(
        create_case("png"),
        admin,
        filename="screen.png",
        content=PNG_BYTES,
        mime_type="image/png",
        category="screenshot",
    )
    assert pdf.status_code == png.status_code == 200
    assert png.json()["category"] == "screenshot"


@pytest.mark.parametrize(
    ("filename", "content", "mime_type", "expected_status"),
    [
        ("malware.exe", b"MZ", "application/x-msdownload", 400),
        ("empty.pdf", b"", "application/pdf", 400),
        ("fake.pdf", PNG_BYTES, "image/png", 400),
    ],
)
def test_invalid_uploads(filename, content, mime_type, expected_status):
    admin = create_user(f"invalid-{filename}", UserRole.ADMIN)
    response = upload(
        create_case(filename),
        admin,
        filename=filename,
        content=content,
        mime_type=mime_type,
    )
    assert response.status_code == expected_status


def test_rejects_oversized_upload(monkeypatch: pytest.MonkeyPatch):
    admin = create_user("oversize", UserRole.ADMIN)
    monkeypatch.setattr(
        "backend.app.services.case_evidence_service.MAX_UPLOAD_SIZE_BYTES", 4
    )
    assert upload(create_case("oversize"), admin, content=b"12345").status_code == 400


def test_description_limit_and_missing_case():
    admin = create_user("bad-metadata", UserRole.ADMIN)
    assert upload(create_case("description"), admin, description="x" * 1001).status_code == 422
    assert upload(999999, admin).status_code == 404


def test_hash_metadata_and_file_persist(setup_database: Path):
    admin = create_user("persist", UserRole.ADMIN)
    result = upload(create_case("persist"), admin, description="  message  ").json()
    with TestingSessionLocal() as db:
        evidence = db.get(CaseEvidence, result["id"])
        assert evidence.description == "message"
        assert evidence.sha256_hash == hashlib.sha256(PDF_BYTES).hexdigest()
        assert evidence.file_size_bytes == len(PDF_BYTES)
    assert (setup_database / result["stored_filename"]).read_bytes() == PDF_BYTES


def test_duplicate_filenames_get_unique_storage_names():
    admin = create_user("duplicates", UserRole.ADMIN)
    case_id = create_case("duplicates")
    first = upload(case_id, admin).json()
    second = upload(case_id, admin).json()
    assert first["original_filename"] == second["original_filename"]
    assert first["stored_filename"] != second["stored_filename"]


def test_list_and_metadata_are_case_scoped():
    admin = create_user("case-scope", UserRole.ADMIN)
    first_case = create_case("scope-one")
    second_case = create_case("scope-two")
    first = upload(first_case, admin).json()
    upload(second_case, admin)
    listing = client.get(
        f"/api/v1/cases/{first_case}/evidence", headers=auth_headers(admin)
    )
    metadata = client.get(
        evidence_url(first_case, first["id"]), headers=auth_headers(admin)
    )
    wrong_case = client.get(
        evidence_url(second_case, first["id"]), headers=auth_headers(admin)
    )
    assert listing.json()["total"] == 1
    assert metadata.status_code == 200
    assert wrong_case.status_code == 404


@pytest.mark.parametrize(
    ("role", "can_read"),
    [
        (UserRole.ADMIN, True),
        (UserRole.FRAUD_ANALYST, True),
        (UserRole.AUDITOR, True),
        (UserRole.VIEWER, False),
    ],
)
def test_download_rbac(role: UserRole, can_read: bool):
    admin = create_user(f"owner-{role.value}", UserRole.ADMIN)
    actor = admin if role == UserRole.ADMIN else create_user(f"reader-{role.value}", role)
    case_id = create_case(f"download-{role.value}")
    evidence = upload(case_id, admin).json()
    response = client.get(
        f"{evidence_url(case_id, evidence['id'])}/download",
        headers=auth_headers(actor),
    )
    assert response.status_code == (200 if can_read else 403)
    if can_read:
        assert response.content == PDF_BYTES
        assert "report.pdf" in response.headers["content-disposition"]
        assert response.headers["x-content-sha256"] == evidence["sha256_hash"]


def test_tampered_download_is_rejected(setup_database: Path):
    admin = create_user("tampered", UserRole.ADMIN)
    case_id = create_case("tampered")
    evidence = upload(case_id, admin).json()
    (setup_database / evidence["stored_filename"]).write_bytes(b"tampered")
    response = client.get(
        f"{evidence_url(case_id, evidence['id'])}/download",
        headers=auth_headers(admin),
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    ("deleter_role", "owns_upload", "expected_status"),
    [
        (UserRole.ADMIN, False, 200),
        (UserRole.FRAUD_ANALYST, True, 200),
        (UserRole.FRAUD_ANALYST, False, 403),
        (UserRole.AUDITOR, False, 403),
        (UserRole.VIEWER, False, 403),
    ],
)
def test_delete_rbac(deleter_role: UserRole, owns_upload: bool, expected_status: int):
    owner = create_user(f"owner-{deleter_role.value}-{owns_upload}", UserRole.FRAUD_ANALYST)
    deleter = owner if owns_upload else create_user(
        f"deleter-{deleter_role.value}-{owns_upload}", deleter_role
    )
    case_id = create_case(f"delete-{deleter_role.value}-{owns_upload}")
    evidence = upload(case_id, owner).json()
    response = client.delete(
        evidence_url(case_id, evidence["id"]), headers=auth_headers(deleter)
    )
    assert response.status_code == expected_status


def test_soft_delete_keeps_file_but_hides_evidence(setup_database: Path):
    admin = create_user("soft-delete", UserRole.ADMIN)
    case_id = create_case("soft-delete")
    evidence = upload(case_id, admin).json()
    deletion = client.delete(
        evidence_url(case_id, evidence["id"]), headers=auth_headers(admin)
    )
    metadata = client.get(
        evidence_url(case_id, evidence["id"]), headers=auth_headers(admin)
    )
    download = client.get(
        f"{evidence_url(case_id, evidence['id'])}/download",
        headers=auth_headers(admin),
    )
    assert deletion.json()["is_deleted"] is True
    assert metadata.status_code == download.status_code == 404
    assert (setup_database / evidence["stored_filename"]).exists()


@pytest.mark.parametrize(
    ("operation", "audit_action", "history_event"),
    [
        ("upload", AuditAction.CASE_EVIDENCE_UPLOAD, EvidenceEvent.UPLOADED),
        ("download", AuditAction.CASE_EVIDENCE_DOWNLOAD, EvidenceEvent.DOWNLOADED),
        ("delete", AuditAction.CASE_EVIDENCE_DELETE, EvidenceEvent.DELETED),
    ],
)
def test_chain_of_custody(operation, audit_action, history_event):
    admin = create_user(f"custody-{operation}", UserRole.ADMIN)
    case_id = create_case(f"custody-{operation}")
    evidence = upload(case_id, admin).json()
    if operation == "download":
        client.get(
            f"{evidence_url(case_id, evidence['id'])}/download",
            headers=auth_headers(admin, "EvidenceBrowser/1.0"),
        )
    elif operation == "delete":
        client.delete(evidence_url(case_id, evidence["id"]), headers=auth_headers(admin))
    with TestingSessionLocal() as db:
        access = db.query(EvidenceAccessLog).filter_by(action=operation).one()
        audit = db.query(AuditLog).filter_by(action=audit_action).one()
        history = db.query(CaseHistory).filter_by(event_type=history_event).one()
        assert access.username == admin.username and access.created_at is not None
        assert audit.resource_type == "case_evidence"
        assert str(PDF_BYTES) not in str(audit.details)
        assert set(history.details) == {"evidence_id", "filename", "category"}


def test_access_log_captures_request_metadata():
    admin = create_user("request-data", UserRole.ADMIN)
    upload(create_case("request-data"), admin)
    with TestingSessionLocal() as db:
        access = db.query(EvidenceAccessLog).filter_by(action="upload").one()
        assert access.ip_address == "testclient"
        assert access.user_agent == "testclient"


def test_denied_access_is_audited():
    viewer = create_user("denied", UserRole.VIEWER)
    response = client.get(
        f"/api/v1/cases/{create_case('denied')}/evidence",
        headers=auth_headers(viewer),
    )
    assert response.status_code == 403
    with TestingSessionLocal() as db:
        audit = db.query(AuditLog).filter_by(
            action=AuditAction.CASE_EVIDENCE_ACCESS_DENIED
        ).one()
        assert audit.status == AuditStatus.DENIED


def test_upload_rolls_back_and_removes_file_on_failure(
    setup_database: Path, monkeypatch: pytest.MonkeyPatch
):
    admin = create_user("rollback", UserRole.ADMIN)

    def fail_history(*args, **kwargs):
        raise RuntimeError("history failure")

    monkeypatch.setattr(
        "backend.app.services.case_evidence_service.create_case_history",
        fail_history,
    )
    with pytest.raises(RuntimeError, match="history failure"):
        upload(create_case("rollback"), admin)
    with TestingSessionLocal() as db:
        assert db.query(CaseEvidence).count() == 0
        assert db.query(EvidenceAccessLog).count() == 0
        assert db.query(AuditLog).count() == 0
    assert list(setup_database.iterdir()) == []
