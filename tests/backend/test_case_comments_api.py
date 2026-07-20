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
from backend.app.models.case_comment import CaseComment
from backend.app.models.case_comment_revision import CaseCommentRevision
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


def create_user(username: str, role: UserRole) -> User:
    with TestingSessionLocal() as db:
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=f"{username} full name",
            hashed_password=hash_password("SecurePassword123!"),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def create_case() -> int:
    with TestingSessionLocal() as db:
        record = FraudScoreRecord(
            transaction_id="comment-source",
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


def create_comment(
    case_id: int,
    actor: User,
    *,
    content: str = "Review the registered device.",
    visibility: str = "internal",
):
    return client.post(
        f"/api/v1/cases/{case_id}/comments",
        json={"content": content, "visibility": visibility},
        headers=auth_headers(actor),
    )


def comment_url(case_id: int, comment_id: int) -> str:
    return f"/api/v1/cases/{case_id}/comments/{comment_id}"


def test_admin_can_create_comment():
    admin = create_user("admin", UserRole.ADMIN)
    response = create_comment(create_case(), admin)
    assert response.status_code == 200
    assert response.json()["author_username"] == admin.username


def test_analyst_can_create_comment():
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    assert create_comment(create_case(), analyst).status_code == 200


def test_auditor_cannot_create_comment():
    auditor = create_user("auditor", UserRole.AUDITOR)
    assert create_comment(create_case(), auditor).status_code == 403


def test_viewer_cannot_create_comment():
    viewer = create_user("viewer", UserRole.VIEWER)
    assert create_comment(create_case(), viewer).status_code == 403


def test_empty_comment_is_rejected():
    admin = create_user("admin", UserRole.ADMIN)
    assert create_comment(create_case(), admin, content="").status_code == 422


def test_whitespace_only_comment_is_rejected():
    admin = create_user("admin", UserRole.ADMIN)
    assert create_comment(create_case(), admin, content="   ").status_code == 422


def test_comment_over_maximum_length_is_rejected():
    admin = create_user("admin", UserRole.ADMIN)
    response = create_comment(create_case(), admin, content="x" * 5001)
    assert response.status_code == 422


def test_comment_for_missing_case_returns_404():
    admin = create_user("admin", UserRole.ADMIN)
    assert create_comment(9999, admin).status_code == 404


def test_comments_are_returned_in_chronological_order():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    first = create_comment(case_id, admin, content="first").json()
    second = create_comment(case_id, admin, content="second").json()
    response = client.get(
        f"/api/v1/cases/{case_id}/comments",
        headers=auth_headers(admin),
    )
    assert [item["id"] for item in response.json()["items"]] == [
        first["id"],
        second["id"],
    ]


def test_admin_can_view_internal_comments():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    response = client.get(
        comment_url(case_id, comment["id"]), headers=auth_headers(admin)
    )
    assert response.status_code == 200


def test_analyst_can_view_internal_comments():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    response = client.get(
        comment_url(case_id, comment["id"]), headers=auth_headers(analyst)
    )
    assert response.status_code == 200


def test_auditor_cannot_view_internal_comments():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    case_id = create_case()
    create_comment(case_id, admin)
    response = client.get(
        f"/api/v1/cases/{case_id}/comments",
        headers=auth_headers(auditor),
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_auditor_can_view_auditor_visible_comments():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    case_id = create_case()
    comment = create_comment(
        case_id, admin, visibility="auditor_visible"
    ).json()
    response = client.get(
        comment_url(case_id, comment["id"]), headers=auth_headers(auditor)
    )
    assert response.status_code == 200


def test_viewer_cannot_list_comments():
    viewer = create_user("viewer", UserRole.VIEWER)
    response = client.get(
        f"/api/v1/cases/{create_case()}/comments",
        headers=auth_headers(viewer),
    )
    assert response.status_code == 403


def test_author_can_edit_own_comment():
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    comment = create_comment(case_id, analyst).json()
    response = client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "Updated review."},
        headers=auth_headers(analyst),
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated review."
    assert response.json()["is_edited"] is True


def test_admin_can_edit_any_comment():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    comment = create_comment(case_id, analyst).json()
    response = client.patch(
        comment_url(case_id, comment["id"]),
        json={"visibility": "auditor_visible"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200


def test_analyst_cannot_edit_another_users_comment():
    author = create_user("author", UserRole.FRAUD_ANALYST)
    other = create_user("other", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    comment = create_comment(case_id, author).json()
    response = client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "Unauthorized edit"},
        headers=auth_headers(other),
    )
    assert response.status_code == 403


def test_auditor_cannot_edit_comment():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    case_id = create_case()
    comment = create_comment(case_id, admin, visibility="auditor_visible").json()
    response = client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "Unauthorized edit"},
        headers=auth_headers(auditor),
    )
    assert response.status_code == 403


def test_unchanged_edit_does_not_create_revision():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin, content="unchanged").json()
    response = client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "unchanged"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    with TestingSessionLocal() as db:
        assert db.query(CaseCommentRevision).count() == 0


def test_edit_creates_revision():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin, content="original").json()
    client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "updated"},
        headers=auth_headers(admin),
    )
    response = client.get(
        f"{comment_url(case_id, comment['id'])}/revisions",
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()[0]["previous_content"] == "original"


def test_author_can_soft_delete_own_comment():
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    comment = create_comment(case_id, analyst).json()
    response = client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(analyst)
    )
    assert response.status_code == 200
    assert response.json()["is_deleted"] is True


def test_admin_can_soft_delete_any_comment():
    admin = create_user("admin", UserRole.ADMIN)
    analyst = create_user("analyst", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    comment = create_comment(case_id, analyst).json()
    response = client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(admin)
    )
    assert response.status_code == 200


def test_analyst_cannot_delete_another_users_comment():
    author = create_user("author", UserRole.FRAUD_ANALYST)
    other = create_user("other", UserRole.FRAUD_ANALYST)
    case_id = create_case()
    comment = create_comment(case_id, author).json()
    response = client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(other)
    )
    assert response.status_code == 403


def test_auditor_cannot_delete_comment():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    case_id = create_case()
    comment = create_comment(case_id, admin, visibility="auditor_visible").json()
    response = client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(auditor)
    )
    assert response.status_code == 403


def test_deleted_comment_returns_deletion_marker():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin, content="sensitive").json()
    client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(admin)
    )
    response = client.get(
        f"/api/v1/cases/{case_id}/comments", headers=auth_headers(admin)
    )
    assert response.json()["items"][0]["content"] == "[comment deleted]"


def test_deleted_comment_cannot_be_edited():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(admin)
    )
    response = client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "restore"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 400


def _history_event(case_id: int, event_type: CaseEvent) -> CaseHistory:
    with TestingSessionLocal() as db:
        event = db.query(CaseHistory).filter_by(
            case_id=case_id, event_type=event_type
        ).one()
        db.expunge(event)
        return event


def test_comment_creation_creates_case_history():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    event = _history_event(case_id, CaseEvent.COMMENT_CREATED)
    assert event.details["comment_id"] == comment["id"]


def test_comment_update_creates_case_history():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "updated"},
        headers=auth_headers(admin),
    )
    assert _history_event(case_id, CaseEvent.COMMENT_UPDATED) is not None


def test_comment_delete_creates_case_history():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(admin)
    )
    assert _history_event(case_id, CaseEvent.COMMENT_DELETED) is not None


def _audit_action(action: AuditAction) -> AuditLog:
    with TestingSessionLocal() as db:
        audit = db.query(AuditLog).filter_by(action=action).one()
        db.expunge(audit)
        return audit


def test_comment_creation_creates_audit_log():
    admin = create_user("admin", UserRole.ADMIN)
    create_comment(create_case(), admin)
    assert _audit_action(AuditAction.CASE_COMMENT_CREATE) is not None


def test_comment_update_creates_audit_log():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    client.patch(
        comment_url(case_id, comment["id"]),
        json={"content": "updated"},
        headers=auth_headers(admin),
    )
    assert _audit_action(AuditAction.CASE_COMMENT_UPDATE) is not None


def test_comment_delete_creates_audit_log():
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    client.delete(
        comment_url(case_id, comment["id"]), headers=auth_headers(admin)
    )
    assert _audit_action(AuditAction.CASE_COMMENT_DELETE) is not None


def test_audit_log_does_not_store_full_comment_content():
    admin = create_user("admin", UserRole.ADMIN)
    secret = "Sensitive investigation narrative"
    create_comment(create_case(), admin, content=secret)
    audit = _audit_action(AuditAction.CASE_COMMENT_CREATE)
    assert secret not in str(audit.details)


def test_comment_from_another_case_returns_404():
    admin = create_user("admin", UserRole.ADMIN)
    first_case = create_case()
    second_case = create_case()
    comment = create_comment(first_case, admin).json()
    response = client.get(
        comment_url(second_case, comment["id"]), headers=auth_headers(admin)
    )
    assert response.status_code == 404


def test_auditor_internal_comment_lookup_returns_404():
    admin = create_user("admin", UserRole.ADMIN)
    auditor = create_user("auditor", UserRole.AUDITOR)
    case_id = create_case()
    comment = create_comment(case_id, admin).json()
    response = client.get(
        comment_url(case_id, comment["id"]), headers=auth_headers(auditor)
    )
    assert response.status_code == 404


def test_comment_creation_rolls_back_when_history_fails(monkeypatch):
    admin = create_user("admin", UserRole.ADMIN)
    case_id = create_case()

    def fail_history(*args, **kwargs):
        raise RuntimeError("history failure")

    monkeypatch.setattr(
        "backend.app.services.case_comment_service.create_case_history",
        fail_history,
    )

    with pytest.raises(RuntimeError, match="history failure"):
        create_comment(case_id, admin)

    with TestingSessionLocal() as db:
        assert db.query(CaseComment).count() == 0
        assert db.query(CaseCommentRevision).count() == 0
        assert db.query(AuditLog).count() == 0
