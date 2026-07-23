from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.session import Base
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.generated_report import GeneratedReport
from backend.app.schemas.report import (
    ReportGenerationRequest,
    ReportListQuery,
)
from backend.app.services.report_export_service import (
    ReportExportService,
    ReportStorageError,
)
from backend.app.services.reporting_service import (
    GeneratedReportNotFoundError,
    GeneratedReportPermissionError,
    GeneratedReportUnavailableError,
    ReportingService,
)


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def seed_case(db) -> int:
    score = FraudScoreRecord(
        transaction_id="reporting-lifecycle",
        model_name="test-model",
        fraud_probability=0.8,
        fraud_prediction=1,
        fraud_threshold=0.5,
        risk_band="high",
        feature_quality={"complete": True},
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
    return fraud_case.id


def generate_report(db, tmp_path: Path) -> tuple[ReportingService, GeneratedReport]:
    case_id = seed_case(db)
    service = ReportingService(
        db,
        export_service=ReportExportService(tmp_path),
    )
    report = service.generate_report(
        case_id=case_id,
        request=ReportGenerationRequest(
            report_type="case_summary",
            export_format="json",
            title="Lifecycle Test Report",
        ),
        requester_user_id=None,
        requester_username="admin",
        requester_role="admin",
    )
    return service, report


def test_generate_list_download_and_integrity(tmp_path: Path):
    with TestingSessionLocal() as db:
        service, report = generate_report(db, tmp_path)

        assert report.status == "completed"
        assert report.file_size_bytes and report.file_size_bytes > 0
        assert report.sha256_hash and len(report.sha256_hash) == 64
        assert Path(report.storage_path).exists()

        result = service.list_reports(
            case_id=report.case_id,
            query=ReportListQuery(limit=10),
        )
        assert result.total == 1
        assert result.items[0].id == report.id

        integrity = service.verify_report_integrity(report_id=report.id)
        assert integrity.valid is True

        download = service.prepare_download(report_id=report.id)
        assert download.filename == report.stored_filename
        assert service.get_report(report_id=report.id).download_count == 1


def test_tampered_report_cannot_be_downloaded(tmp_path: Path):
    with TestingSessionLocal() as db:
        service, report = generate_report(db, tmp_path)
        Path(report.storage_path).write_text("tampered", encoding="utf-8")

        with pytest.raises(GeneratedReportUnavailableError):
            service.prepare_download(report_id=report.id)


def test_soft_delete_permissions_visibility_and_restore(tmp_path: Path):
    with TestingSessionLocal() as db:
        service, report = generate_report(db, tmp_path)

        with pytest.raises(GeneratedReportPermissionError):
            service.soft_delete_report(
                report_id=report.id,
                requester_user_id=None,
                requester_username="analyst",
                requester_role="fraud_analyst",
            )

        service.soft_delete_report(
            report_id=report.id,
            requester_user_id=None,
            requester_username="admin",
            requester_role="admin",
            remove_file=False,
        )
        with pytest.raises(GeneratedReportNotFoundError):
            service.get_report(report_id=report.id)

        restored = service.restore_report(
            report_id=report.id,
            requester_role="admin",
        )
        assert restored.status == "completed"
        assert restored.is_deleted is False


def test_delete_with_file_removal_prevents_restore(tmp_path: Path):
    with TestingSessionLocal() as db:
        service, report = generate_report(db, tmp_path)
        storage_path = Path(report.storage_path)
        service.soft_delete_report(
            report_id=report.id,
            requester_user_id=None,
            requester_username="admin",
            requester_role="admin",
        )

        assert not storage_path.exists()
        with pytest.raises(GeneratedReportUnavailableError):
            service.restore_report(
                report_id=report.id,
                requester_role="admin",
            )


def test_generation_failure_is_persisted(tmp_path: Path):
    class FailingExportService(ReportExportService):
        def export(self, **kwargs):
            raise ReportStorageError("Storage unavailable.")

    with TestingSessionLocal() as db:
        case_id = seed_case(db)
        service = ReportingService(
            db,
            export_service=FailingExportService(tmp_path),
        )

        with pytest.raises(ReportStorageError):
            service.generate_report(
                case_id=case_id,
                request=ReportGenerationRequest(
                    report_type="case_summary",
                    export_format="json",
                ),
                requester_user_id=None,
                requester_username="admin",
                requester_role="admin",
            )

        failed = db.scalar(select(GeneratedReport))
        assert failed is not None
        assert failed.status == "failed"
        assert failed.failure_message == "Storage unavailable."


def test_missing_report_is_rejected(tmp_path: Path):
    with TestingSessionLocal() as db:
        service = ReportingService(
            db,
            export_service=ReportExportService(tmp_path),
        )

        with pytest.raises(GeneratedReportNotFoundError):
            service.get_report(report_id=999999)
