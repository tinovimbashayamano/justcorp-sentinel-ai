"""
Development bootstrap utility.

Production and deployed database schema changes must be applied through
Alembic migrations. SQLAlchemy create_all() does not modify existing tables.
"""

from backend.app.db.session import Base, engine
from backend.app.models.audit_log import AuditLog
from backend.app.models.case_comment import CaseComment
from backend.app.models.case_comment_revision import CaseCommentRevision
from backend.app.models.case_history import CaseHistory
from backend.app.models.case_evidence import CaseEvidence
from backend.app.models.evidence_access_log import EvidenceAccessLog
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.generated_report import GeneratedReport
from backend.app.models.investigation_task import InvestigationTask
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
    print(f"Registered table: {FraudScoreRecord.__tablename__}")
    print(f"Registered table: {FraudCaseReview.__tablename__}")
    print(f"Registered table: {User.__tablename__}")
    print(f"Registered table: {RefreshToken.__tablename__}")
    print(f"Registered table: {AuditLog.__tablename__}")
    print(f"Registered table: {CaseHistory.__tablename__}")
    print(f"Registered table: {CaseComment.__tablename__}")
    print(f"Registered table: {CaseCommentRevision.__tablename__}")
    print(f"Registered table: {CaseEvidence.__tablename__}")
    print(f"Registered table: {EvidenceAccessLog.__tablename__}")
    print(f"Registered table: {InvestigationTask.__tablename__}")
    print(f"Registered table: {GeneratedReport.__tablename__}")


if __name__ == "__main__":
    init_db()
