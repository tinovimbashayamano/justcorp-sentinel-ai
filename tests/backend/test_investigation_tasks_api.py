from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.audit import AuditAction
from backend.app.core.investigation_tasks import InvestigationTaskEvent
from backend.app.core.security import create_access_token
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.case_history import CaseHistory
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.investigation_task import InvestigationTask
from backend.app.models.user import User, UserRole


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
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
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


def create_case(label: str = "task-source") -> int:
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
        fraud_case = FraudCaseReview(
            fraud_score_record_id=record.id,
            case_status="open",
            priority="medium",
            analyst_decision="pending",
        )
        db.add(fraud_case)
        db.commit()
        db.refresh(fraud_case)
        return fraud_case.id


def tasks_url(case_id: int) -> str:
    return f"/api/v1/fraud-cases/{case_id}/tasks"


def task_url(case_id: int, task_id: int) -> str:
    return f"{tasks_url(case_id)}/{task_id}"


def create_task(
    case_id: int,
    actor: User,
    *,
    title: str = "Review customer account activity",
    priority: str = "high",
    assigned_to_user_id: int | None = None,
):
    payload: dict[str, object] = {
        "title": title,
        "description": "Check high-risk transfers.",
        "priority": priority,
    }
    if assigned_to_user_id is not None:
        payload["assigned_to_user_id"] = assigned_to_user_id
    return client.post(
        tasks_url(case_id),
        json=payload,
        headers=auth_headers(actor),
    )


def add_task_directly(
    case_id: int,
    actor: User,
    *,
    task_status: str = "pending",
    due_at: datetime | None = None,
    is_deleted: bool = False,
) -> InvestigationTask:
    with TestingSessionLocal() as db:
        task = InvestigationTask(
            case_id=case_id,
            title=f"Direct {task_status} task",
            status=task_status,
            priority="medium",
            due_at=due_at,
            created_by_user_id=actor.id,
            created_by_username=actor.username,
            is_deleted=is_deleted,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        db.expunge(task)
        return task


def test_admin_can_create_task():
    admin = create_user("admin", UserRole.ADMIN)
    response = create_task(create_case(), admin)
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_analyst_can_list_tasks():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    create_task(case_id, admin)
    response = client.get(tasks_url(case_id), headers=auth_headers(analyst))
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_auditor_can_read_tasks():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.get(
        task_url(case_id, task["id"]), headers=auth_headers(auditor)
    )
    assert response.status_code == 200


def test_auditor_cannot_create_task():
    auditor = create_user("auditor", UserRole.AUDITOR)
    assert create_task(create_case(), auditor).status_code == 403


def test_viewer_cannot_list_tasks():
    viewer = create_user("viewer", UserRole.VIEWER)
    response = client.get(tasks_url(create_case()), headers=auth_headers(viewer))
    assert response.status_code == 403


def test_create_task_rejects_unknown_assignee():
    admin = create_user("admin", UserRole.ADMIN)
    response = create_task(create_case(), admin, assigned_to_user_id=99999)
    assert response.status_code == 404


def test_create_task_rejects_invalid_assignee_role():
    admin = create_user("admin", UserRole.ADMIN)
    viewer = create_user("viewer", UserRole.VIEWER)
    response = create_task(
        create_case(), admin, assigned_to_user_id=viewer.id
    )
    assert response.status_code == 400


def test_create_task_rejects_inactive_assignee():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user(
        "inactive", UserRole.FRAUD_ANALYST, is_active=False
    )
    response = create_task(
        create_case(), admin, assigned_to_user_id=analyst.id
    )
    assert response.status_code == 400


def test_task_title_is_trimmed():
    admin = create_user("admin", UserRole.ADMIN)
    response = create_task(
        create_case(), admin, title="   Verify customer identity   "
    )
    assert response.json()["title"] == "Verify customer identity"


def test_admin_can_update_task():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.patch(
        task_url(case_id, task["id"]),
        json={"title": "Review linked customer devices", "priority": "critical"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["priority"] == "critical"


def test_auditor_cannot_update_task():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.patch(
        task_url(case_id, task["id"]),
        json={"title": "Unauthorized change"},
        headers=auth_headers(auditor),
    )
    assert response.status_code == 403


def test_admin_can_assign_task():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.patch(
        f"{task_url(case_id, task['id'])}/assignment",
        json={"assigned_to_user_id": analyst.id},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["assigned_to_username"] == analyst.username


def test_admin_can_reassign_task():
    admin = create_user("admin", UserRole.ADMIN)
    first = create_user("first", UserRole.FRAUD_ANALYST)
    second = create_user("second", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    task = create_task(case_id, admin, assigned_to_user_id=first.id).json()
    response = client.patch(
        f"{task_url(case_id, task['id'])}/assignment",
        json={"assigned_to_user_id": second.id},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["assigned_to_user_id"] == second.id


def test_admin_can_unassign_task():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    task = create_task(case_id, admin, assigned_to_user_id=analyst.id).json()
    response = client.patch(
        f"{task_url(case_id, task['id'])}/assignment",
        json={"assigned_to_user_id": None},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["assigned_to_user_id"] is None


def test_same_assignment_is_rejected():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    task = create_task(case_id, admin, assigned_to_user_id=analyst.id).json()
    response = client.patch(
        f"{task_url(case_id, task['id'])}/assignment",
        json={"assigned_to_user_id": analyst.id},
        headers=auth_headers(admin),
    )
    assert response.status_code == 409


def test_assigned_analyst_can_start_task():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    task = create_task(case_id, admin, assigned_to_user_id=analyst.id).json()
    response = client.patch(
        f"{task_url(case_id, task['id'])}/status",
        json={"status": "in_progress", "reason": "Work started"},
        headers=auth_headers(analyst),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_unassigned_analyst_cannot_start_task():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.patch(
        f"{task_url(case_id, task['id'])}/status",
        json={"status": "in_progress"},
        headers=auth_headers(analyst),
    )
    assert response.status_code == 403


def test_pending_task_cannot_be_completed():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.post(
        f"{task_url(case_id, task['id'])}/complete",
        json={"completion_note": "Work completed successfully"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 409


def test_in_progress_task_can_be_completed():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    client.patch(
        f"{task_url(case_id, task['id'])}/status",
        json={"status": "in_progress"},
        headers=auth_headers(admin),
    )
    response = client.post(
        f"{task_url(case_id, task['id'])}/complete",
        json={"completion_note": "Reviewed and resolved"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["completed_by_username"] == admin.username


def test_completion_requires_note():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.post(
        f"{task_url(case_id, task['id'])}/complete",
        json={"completion_note": " "},
        headers=auth_headers(admin),
    )
    assert response.status_code == 422


def test_privileged_admin_can_cancel_pending_task():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.post(
        f"{task_url(case_id, task['id'])}/cancel",
        json={"cancellation_reason": "No longer required"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_analyst_cannot_cancel_task():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    task = create_task(case_id, admin, assigned_to_user_id=analyst.id).json()
    response = client.post(
        f"{task_url(case_id, task['id'])}/cancel",
        json={"cancellation_reason": "Unauthorized cancellation"},
        headers=auth_headers(analyst),
    )
    assert response.status_code == 403


def test_completed_task_cannot_be_modified():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = add_task_directly(case_id, admin, task_status="completed")
    response = client.patch(
        task_url(case_id, task.id),
        json={"title": "Changed completed task"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 409


def test_cancelled_task_cannot_be_modified():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = add_task_directly(case_id, admin, task_status="cancelled")
    response = client.patch(
        task_url(case_id, task.id),
        json={"priority": "critical"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 409


def test_invalid_status_transition_returns_409():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.patch(
        f"{task_url(case_id, task['id'])}/status",
        json={"status": "pending"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 409


def test_overdue_flag_is_true_for_active_past_due_task():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = add_task_directly(
        case_id,
        admin,
        due_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    response = client.get(
        task_url(case_id, task.id), headers=auth_headers(admin)
    )
    assert response.json()["is_overdue"] is True


def test_completed_task_is_not_overdue():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = add_task_directly(
        case_id,
        admin,
        task_status="completed",
        due_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    response = client.get(
        task_url(case_id, task.id), headers=auth_headers(admin)
    )
    assert response.json()["is_overdue"] is False


def test_overdue_filter_returns_only_overdue_tasks():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    overdue = add_task_directly(
        case_id,
        admin,
        due_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    add_task_directly(
        case_id,
        admin,
        due_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    response = client.get(
        f"{tasks_url(case_id)}?overdue_only=true",
        headers=auth_headers(admin),
    )
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == overdue.id


def test_admin_can_soft_delete_task():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    response = client.delete(
        task_url(case_id, task["id"]), headers=auth_headers(admin)
    )
    assert response.status_code == 200
    assert response.json()["is_deleted"] is True


def test_deleted_task_is_not_listed():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    client.delete(task_url(case_id, task["id"]), headers=auth_headers(admin))
    response = client.get(tasks_url(case_id), headers=auth_headers(admin))
    assert response.json()["items"] == []


def test_deleted_task_returns_404():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    client.delete(task_url(case_id, task["id"]), headers=auth_headers(admin))
    response = client.get(
        task_url(case_id, task["id"]), headers=auth_headers(admin)
    )
    assert response.status_code == 404


def test_task_from_another_case_returns_404():
    admin = create_user("admin", UserRole.ADMIN)
    first_case = create_case("first")
    second_case = create_case("second")
    task = create_task(first_case, admin).json()
    response = client.get(
        task_url(second_case, task["id"]), headers=auth_headers(admin)
    )
    assert response.status_code == 404


def test_task_creation_writes_audit_log():
    admin = create_user("admin", UserRole.ADMIN)
    task = create_task(create_case(), admin).json()
    with TestingSessionLocal() as db:
        log = db.query(AuditLog).filter_by(
            action=AuditAction.INVESTIGATION_TASK_CREATED
        ).one()
        assert log.resource_id == str(task["id"])
        assert "description" not in log.details


def test_task_creation_writes_case_history():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    with TestingSessionLocal() as db:
        event = db.query(CaseHistory).filter_by(
            event_type=InvestigationTaskEvent.CREATED
        ).one()
        assert event.case_id == case_id
        assert event.details["task_id"] == task["id"]


def test_task_completion_writes_audit_and_history():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    task = create_task(case_id, admin).json()
    client.patch(
        f"{task_url(case_id, task['id'])}/status",
        json={"status": "in_progress"},
        headers=auth_headers(admin),
    )
    client.post(
        f"{task_url(case_id, task['id'])}/complete",
        json={"completion_note": "Resolved successfully"},
        headers=auth_headers(admin),
    )
    with TestingSessionLocal() as db:
        assert db.query(AuditLog).filter_by(
            action=AuditAction.INVESTIGATION_TASK_COMPLETED
        ).one()
        assert db.query(CaseHistory).filter_by(
            event_type=InvestigationTaskEvent.COMPLETED
        ).one()


def test_task_creation_rolls_back_if_audit_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()

    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit failure")

    monkeypatch.setattr(
        "backend.app.api.investigation_tasks.create_audit_log",
        fail_audit,
    )
    with pytest.raises(RuntimeError, match="audit failure"):
        create_task(case_id, admin)
    with TestingSessionLocal() as db:
        assert db.query(InvestigationTask).count() == 0
        assert db.query(CaseHistory).count() == 0
