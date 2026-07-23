from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.app.api.reports as reports_api
from backend.app.core.security import create_access_token
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User, UserRole
from backend.app.services.report_export_service import ReportExportService
from backend.app.services.reporting_service import ReportingService


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
client = TestClient(app)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    def reporting_service_factory(db):
        return ReportingService(
            db,
            export_service=ReportExportService(tmp_path / "reports"),
        )

    monkeypatch.setattr(
        reports_api,
        "ReportingService",
        reporting_service_factory,
    )
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def create_user(
    username: str,
    role: UserRole,
    *,
    is_active: bool = True,
) -> User:
    with TestingSessionLocal() as db:
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password="not-used-by-token-tests",
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def create_case(label: str = "report-api") -> int:
    with TestingSessionLocal() as db:
        score = FraudScoreRecord(
            transaction_id=label,
            model_name="test-model",
            fraud_probability=0.9,
            fraud_prediction=1,
            fraud_threshold=0.5,
            risk_band="high",
            feature_quality={},
        )
        db.add(score)
        db.flush()
        fraud_case = FraudCaseReview(
            fraud_score_record_id=score.id,
            case_status="open",
            priority="high",
            analyst_decision="pending",
        )
        db.add(fraud_case)
        db.commit()
        db.refresh(fraud_case)
        return fraud_case.id


def generate_report(case_id: int, actor: User, export_format: str = "json"):
    return client.post(
        f"/api/v1/reports/cases/{case_id}",
        json={
            "report_type": "case_summary",
            "export_format": export_format,
            "title": "API Verification Report",
        },
        headers=auth_headers(actor),
    )


def test_admin_can_generate_list_and_get_report():
    admin = create_user("reportadmin", UserRole.ADMIN)
    case_id = create_case()

    generated = generate_report(case_id, admin)
    assert generated.status_code == 201
    body = generated.json()
    report_id = body["report"]["id"]
    assert body["message"] == "Report generated successfully."
    assert body["report"]["status"] == "completed"
    assert body["report"]["is_downloadable"] is True

    listed = client.get(
        f"/api/v1/reports/cases/{case_id}?status=completed&limit=10",
        headers=auth_headers(admin),
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    all_reports = client.get(
        "/api/v1/reports?report_type=case_summary&export_format=json",
        headers=auth_headers(admin),
    )
    assert all_reports.status_code == 200
    assert all_reports.json()["items"][0]["id"] == report_id

    metadata = client.get(
        f"/api/v1/reports/{report_id}",
        headers=auth_headers(admin),
    )
    assert metadata.status_code == 200
    assert metadata.json()["case_id"] == case_id


def test_download_returns_integrity_and_cache_headers():
    admin = create_user("downloadadmin", UserRole.ADMIN)
    report_id = generate_report(create_case(), admin).json()["report"]["id"]

    response = client.get(
        f"/api/v1/reports/{report_id}/download",
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["x-report-id"] == str(report_id)
    assert len(response.headers["x-report-sha256"]) == 64
    assert response.headers["cache-control"].startswith("private, no-store")
    assert response.headers["x-content-type-options"] == "nosniff"

    metadata = client.get(
        f"/api/v1/reports/{report_id}",
        headers=auth_headers(admin),
    )
    assert metadata.json()["download_count"] == 1


def test_integrity_is_available_to_admin_and_auditor_only():
    admin = create_user("integrityadmin", UserRole.ADMIN)
    auditor = create_user("integrityauditor", UserRole.AUDITOR)
    analyst = create_user("integrityanalyst", UserRole.FRAUD_ANALYST)
    report_id = generate_report(create_case(), admin).json()["report"]["id"]

    assert client.get(
        f"/api/v1/reports/{report_id}/integrity",
        headers=auth_headers(admin),
    ).json()["valid"] is True
    assert client.get(
        f"/api/v1/reports/{report_id}/integrity",
        headers=auth_headers(auditor),
    ).status_code == 200
    assert client.get(
        f"/api/v1/reports/{report_id}/integrity",
        headers=auth_headers(analyst),
    ).status_code == 403


def test_admin_can_soft_delete_and_restore_when_file_is_retained():
    admin = create_user("restoreadmin", UserRole.ADMIN)
    analyst = create_user("restoreanalyst", UserRole.FRAUD_ANALYST)
    report_id = generate_report(create_case(), admin).json()["report"]["id"]

    denied = client.delete(
        f"/api/v1/reports/{report_id}?remove_file=false",
        headers=auth_headers(analyst),
    )
    assert denied.status_code == 403

    deleted = client.delete(
        f"/api/v1/reports/{report_id}?remove_file=false",
        headers=auth_headers(admin),
    )
    assert deleted.status_code == 200

    assert client.get(
        f"/api/v1/reports/{report_id}",
        headers=auth_headers(admin),
    ).status_code == 404
    assert client.get(
        f"/api/v1/reports/{report_id}?include_deleted=true",
        headers=auth_headers(analyst),
    ).status_code == 403

    deleted_metadata = client.get(
        f"/api/v1/reports/{report_id}?include_deleted=true",
        headers=auth_headers(admin),
    )
    assert deleted_metadata.status_code == 200
    assert deleted_metadata.json()["is_deleted"] is True

    restored = client.post(
        f"/api/v1/reports/{report_id}/restore",
        headers=auth_headers(admin),
    )
    assert restored.status_code == 200
    assert restored.json()["report"]["status"] == "completed"


def test_viewer_and_inactive_users_are_denied():
    viewer = create_user("reportviewer", UserRole.VIEWER)
    inactive = create_user(
        "inactiveanalyst",
        UserRole.FRAUD_ANALYST,
        is_active=False,
    )
    case_id = create_case()

    assert generate_report(case_id, viewer).status_code == 403
    assert client.get(
        "/api/v1/reports",
        headers=auth_headers(viewer),
    ).status_code == 403
    assert generate_report(case_id, inactive).status_code == 403


def test_generation_error_responses_are_stable():
    admin = create_user("erroradmin", UserRole.ADMIN)
    analyst = create_user("erroranalyst", UserRole.FRAUD_ANALYST)

    missing = generate_report(999999, admin)
    assert missing.status_code == 404

    invalid_combination = client.post(
        f"/api/v1/reports/cases/{create_case()}",
        json={
            "report_type": "complete_case",
            "export_format": "csv",
        },
        headers=auth_headers(admin),
    )
    assert invalid_combination.status_code == 422

    audit_denied = client.post(
        f"/api/v1/reports/cases/{create_case('audit-denied')}",
        json={
            "report_type": "audit_summary",
            "export_format": "json",
            "include_audit_logs": True,
        },
        headers=auth_headers(analyst),
    )
    assert audit_denied.status_code == 403
