from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.session import Base
from backend.app.models.audit_log import AuditLog
from backend.app.models.case_comment import CaseComment
from backend.app.models.case_evidence import CaseEvidence
from backend.app.models.case_history import CaseHistory
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.investigation_task import InvestigationTask
from backend.app.models.user import User  # noqa: F401
from backend.app.schemas.report import ReportGenerationOptions
from backend.app.services.report_data_service import (
    ReportCaseNotFoundError,
    ReportDataPermissionError,
    ReportDataService,
    UnsupportedReportTypeError,
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


def seed_case(db: Session) -> int:
    score = FraudScoreRecord(
        transaction_id="report-transaction",
        model_name="report-test-model",
        fraud_probability=0.91,
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
    db.flush()

    db.add_all(
        [
            CaseComment(
                case_id=fraud_case.id,
                author_username="analyst",
                content="Visible investigation comment",
                visibility="auditor_visible",
            ),
            CaseComment(
                case_id=fraud_case.id,
                author_username="analyst",
                content="Internal investigation comment",
                visibility="internal",
            ),
            CaseHistory(
                case_id=fraud_case.id,
                actor_username="analyst",
                event_type="case.updated",
                details={"field": "priority"},
            ),
            InvestigationTask(
                case_id=fraud_case.id,
                title="Review device history",
                status="pending",
                priority="critical",
                due_at=datetime.now(timezone.utc) - timedelta(days=1),
                created_by_username="admin",
            ),
            CaseEvidence(
                case_id=fraud_case.id,
                uploader_username="analyst",
                original_filename="evidence.pdf",
                stored_filename="generated-evidence.pdf",
                storage_path="storage/evidence/generated-evidence.pdf",
                mime_type="application/pdf",
                category="document",
                file_size_bytes=512,
                sha256_hash="a" * 64,
            ),
            AuditLog(
                actor_username="admin",
                action="case.updated",
                status="success",
                resource_type="fraud_case",
                resource_id=str(fraud_case.id),
            ),
        ]
    )
    db.commit()
    return fraud_case.id


def test_case_summary_uses_case_score_reference_and_filters_internal_comments():
    with TestingSessionLocal() as db:
        case_id = seed_case(db)
        report = ReportDataService(db).build_report_data(
            case_id=case_id,
            report_type="case_summary",
            requester_role="fraud_analyst",
        )

    assert report["statistics"] == {
        "fraud_score_count": 1,
        "comment_count": 1,
    }
    assert report["fraud_scores"][0]["transaction_id"] == "report-transaction"
    assert report["comments"][0]["visibility"] == "auditor_visible"


def test_complete_report_aggregates_related_data_and_statistics():
    with TestingSessionLocal() as db:
        case_id = seed_case(db)
        report = ReportDataService(db).build_report_data(
            case_id=case_id,
            report_type="complete_case",
            options=ReportGenerationOptions(
                include_sensitive_data=True,
                include_internal_comments=True,
                include_audit_logs=True,
            ),
            requester_role="admin",
            requester_user_id=1,
            requester_username="admin",
        )

    assert report["metadata"]["generated_by"]["username"] == "admin"
    assert report["statistics"]["fraud_score_count"] == 1
    assert report["statistics"]["history_event_count"] == 1
    assert report["statistics"]["task_count"] == 1
    assert report["statistics"]["evidence_count"] == 1
    assert report["statistics"]["comment_count"] == 2
    assert report["statistics"]["audit_log_count"] == 1
    assert report["evidence"][0]["storage_path"].startswith("storage/evidence/")


def test_evidence_inventory_excludes_storage_path_by_default():
    with TestingSessionLocal() as db:
        case_id = seed_case(db)
        report = ReportDataService(db).build_report_data(
            case_id=case_id,
            report_type="evidence_inventory",
            requester_role="fraud_analyst",
        )

    assert report["statistics"]["total_file_size_bytes"] == 512
    assert "storage_path" not in report["evidence"][0]


def test_task_summary_calculates_counts_and_overdue_state():
    with TestingSessionLocal() as db:
        case_id = seed_case(db)
        report = ReportDataService(db).build_report_data(
            case_id=case_id,
            report_type="task_summary",
            requester_role="fraud_analyst",
        )

    assert report["statistics"]["total_tasks"] == 1
    assert report["statistics"]["overdue_tasks"] == 1
    assert report["statistics"]["status_counts"] == {"pending": 1}


@pytest.mark.parametrize(
    "options",
    [
        ReportGenerationOptions(include_sensitive_data=True),
        ReportGenerationOptions(include_internal_comments=True),
        ReportGenerationOptions(include_audit_logs=True),
    ],
)
def test_viewer_cannot_request_restricted_options(options):
    with TestingSessionLocal() as db:
        case_id = seed_case(db)
        with pytest.raises(ReportDataPermissionError):
            ReportDataService(db).build_report_data(
                case_id=case_id,
                report_type="complete_case",
                options=options,
                requester_role="viewer",
            )


def test_analyst_cannot_request_detailed_audit_logs():
    with TestingSessionLocal() as db:
        case_id = seed_case(db)
        with pytest.raises(ReportDataPermissionError):
            ReportDataService(db).build_report_data(
                case_id=case_id,
                report_type="audit_summary",
                options=ReportGenerationOptions(include_audit_logs=True),
                requester_role="fraud_analyst",
            )


def test_missing_case_and_unsupported_type_raise_domain_errors():
    with TestingSessionLocal() as db:
        service = ReportDataService(db)
        with pytest.raises(ReportCaseNotFoundError):
            service.build_report_data(
                case_id=999,
                report_type="case_summary",
                requester_role="admin",
            )

        case_id = seed_case(db)
        with pytest.raises(UnsupportedReportTypeError):
            service.build_report_data(
                case_id=case_id,
                report_type="unsupported",
                requester_role="admin",
            )
