import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.audit import AuditAction
from backend.app.core.case_history import CaseEvent
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.case_history import CaseHistory
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User, UserRole


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


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
            full_name=f"{username} full name",
            hashed_password=hash_password("SecurePassword123!"),
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


def create_case(*, status: str = "open", assignee_id: int | None = None) -> int:
    with TestingSessionLocal() as db:
        record = FraudScoreRecord(
            transaction_id=f"assignment-source-{status}-{assignee_id}",
            model_name="test-model",
            fraud_probability=0.9,
            fraud_prediction=1,
            fraud_threshold=0.84,
            risk_band="high",
            feature_quality={},
        )
        db.add(record)
        db.flush()
        fraud_case = FraudCaseReview(
            fraud_score_record_id=record.id,
            case_status=status,
            priority="medium",
            analyst_decision="pending",
            assigned_to_user_id=assignee_id,
        )
        db.add(fraud_case)
        db.commit()
        db.refresh(fraud_case)
        return fraud_case.id


def assignment_request(case_id: int, assignee: User, actor: User):
    return client.patch(
        f"/api/v1/cases/{case_id}/assignment",
        json={"assigned_to_user_id": assignee.id},
        headers=auth_headers(actor),
    )


def test_admin_can_assign_case():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    response = assignment_request(create_case(), analyst, admin)
    assert response.status_code == 200


def test_assignment_to_fraud_analyst_succeeds():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    response = assignment_request(create_case(), analyst, admin)
    assert response.json()["assigned_to_user_id"] == analyst.id
    assert response.json()["assigned_to_username"] == analyst.username


def test_assignment_to_admin_is_rejected():
    admin = create_user("admin", UserRole.ADMIN)
    response = assignment_request(create_case(), admin, admin)
    assert response.status_code == 400


def test_assignment_to_auditor_is_rejected():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    response = assignment_request(create_case(), auditor, admin)
    assert response.status_code == 400


def test_assignment_to_inactive_user_is_rejected():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user(
        "analyst", UserRole.FRAUD_ANALYST, is_active=False
    )
    response = assignment_request(create_case(), analyst, admin)
    assert response.status_code == 400


def test_assignment_to_missing_user_returns_404():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    response = client.patch(
        f"/api/v1/cases/{case_id}/assignment",
        json={"assigned_to_user_id": 9999},
        headers=auth_headers(admin),
    )
    assert response.status_code == 404


def test_reassignment_updates_owner():
    admin = create_user("admin", UserRole.ADMIN)
    first = create_user("first", UserRole.FRAUD_ANALYST)
    second = create_user("second", UserRole.FRAUD_ANALYST)
    case_id = create_case(assignee_id=first.id)
    response = assignment_request(case_id, second, admin)
    assert response.json()["assigned_to_user_id"] == second.id
    assert response.json()["assigned_to_username"] == second.username


def test_unassignment_removes_owner():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case(assignee_id=analyst.id)
    response = client.delete(
        f"/api/v1/cases/{case_id}/assignment",
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["assigned_to_user_id"] is None


def test_same_assignment_does_not_duplicate_history():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    assert assignment_request(case_id, analyst, admin).status_code == 200
    assert assignment_request(case_id, analyst, admin).status_code == 200
    with TestingSessionLocal() as db:
        count = db.query(CaseHistory).filter_by(case_id=case_id).count()
    assert count == 1


def test_assignment_creates_case_history():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    assignment_request(case_id, analyst, admin)
    with TestingSessionLocal() as db:
        history = db.query(CaseHistory).filter_by(case_id=case_id).one()
    assert history.event_type == CaseEvent.ASSIGNED
    assert history.details["new_assignee_username"] == analyst.username


def test_reassignment_creates_case_history():
    admin = create_user("admin", UserRole.ADMIN)
    first = create_user("first", UserRole.FRAUD_ANALYST)
    second = create_user("second", UserRole.FRAUD_ANALYST)
    case_id = create_case(assignee_id=first.id)
    assignment_request(case_id, second, admin)
    with TestingSessionLocal() as db:
        history = db.query(CaseHistory).filter_by(case_id=case_id).one()
    assert history.event_type == CaseEvent.REASSIGNED
    assert history.details["old_assignee_user_id"] == first.id


def test_unassignment_creates_case_history():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case(assignee_id=analyst.id)
    client.delete(
        f"/api/v1/cases/{case_id}/assignment",
        headers=auth_headers(admin),
    )
    with TestingSessionLocal() as db:
        history = db.query(CaseHistory).filter_by(case_id=case_id).one()
    assert history.event_type == CaseEvent.UNASSIGNED
    assert history.details["reason"] == "manual_unassignment"


def test_assignment_creates_audit_log():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    assignment_request(case_id, analyst, admin)
    with TestingSessionLocal() as db:
        audit = db.query(AuditLog).filter_by(resource_id=str(case_id)).one()
    assert audit.action == AuditAction.CASE_ASSIGNED
    assert audit.resource_type == "fraud_case"


def test_fraud_analyst_cannot_assign_case():
    actor = create_user("actor", UserRole.FRAUD_ANALYST)
    target = create_user("target", UserRole.FRAUD_ANALYST)
    assert assignment_request(create_case(), target, actor).status_code == 403


def test_auditor_cannot_assign_case():
    actor = create_user("actor", UserRole.AUDITOR)
    target = create_user("target", UserRole.FRAUD_ANALYST)
    assert assignment_request(create_case(), target, actor).status_code == 403


def test_viewer_cannot_assign_case():
    actor = create_user("actor", UserRole.VIEWER)
    target = create_user("target", UserRole.FRAUD_ANALYST)
    assert assignment_request(create_case(), target, actor).status_code == 403


def test_filter_cases_by_assignee():
    admin = create_user("admin", UserRole.ADMIN)
    first = create_user("first", UserRole.FRAUD_ANALYST)
    second = create_user("second", UserRole.FRAUD_ANALYST)
    expected_id = create_case(assignee_id=first.id)
    create_case(assignee_id=second.id)
    response = client.get(
        f"/api/v1/fraud/cases?assigned_to_user_id={first.id}",
        headers=auth_headers(admin),
    )
    assert [item["id"] for item in response.json()] == [expected_id]


def test_filter_unassigned_cases():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    expected_id = create_case()
    create_case(assignee_id=analyst.id)
    response = client.get(
        "/api/v1/fraud/cases?unassigned=true",
        headers=auth_headers(admin),
    )
    assert [item["id"] for item in response.json()] == [expected_id]


def test_conflicting_assignment_filters_return_422():
    admin = create_user("admin", UserRole.ADMIN)
    response = client.get(
        "/api/v1/fraud/cases?assigned_to_user_id=1&unassigned=true",
        headers=auth_headers(admin),
    )
    assert response.status_code == 422


def test_workload_endpoint_returns_active_case_counts():
    admin = create_user("admin", UserRole.ADMIN)
    busy = create_user("busy", UserRole.FRAUD_ANALYST)
    available = create_user("available", UserRole.FRAUD_ANALYST)
    create_case(status="open", assignee_id=busy.id)
    create_case(status="investigating", assignee_id=busy.id)
    create_case(status="closed", assignee_id=busy.id)
    response = client.get(
        "/api/v1/cases/assignments/workload",
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    workloads = response.json()
    assert [item["analyst_id"] for item in workloads] == [available.id, busy.id]
    assert workloads[1]["open_cases"] == 1
    assert workloads[1]["investigating_cases"] == 1
    assert workloads[1]["total_active_cases"] == 2
