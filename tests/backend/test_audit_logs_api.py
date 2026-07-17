import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.user import User, UserRole
from backend.app.services.audit_service import create_audit_log


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
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
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

PASSWORD = "SecurePassword123!"
NEW_PASSWORD = "NewSecurePassword456!"


def create_user(
    username: str,
    role: UserRole = UserRole.VIEWER,
) -> User:
    with TestingSessionLocal() as db:
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=f"{username} user",
            hashed_password=hash_password(PASSWORD),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)

        return user


def auth_headers(user: User) -> dict[str, str]:
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {access_token}",
    }


def register_user(
    username: str = "audituser",
):
    return client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": PASSWORD,
            "full_name": "Audit User",
        },
    )


def login_user(
    username: str = "audituser",
    password: str = PASSWORD,
):
    return client.post(
        "/api/v1/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )


def get_audit_logs(
    action: AuditAction | None = None,
) -> list[AuditLog]:
    with TestingSessionLocal() as db:
        query = db.query(AuditLog)

        if action is not None:
            query = query.filter(AuditLog.action == action.value)

        logs = query.order_by(AuditLog.id).all()

        for log in logs:
            db.expunge(log)

        return logs


def create_fraud_score_record() -> FraudScoreRecord:
    with TestingSessionLocal() as db:
        record = FraudScoreRecord(
            transaction_id="case-source-001",
            model_name="test-model",
            fraud_probability=0.95,
            fraud_prediction=1,
            fraud_threshold=0.84,
            risk_band="high",
            feature_quality={},
        )

        db.add(record)
        db.commit()
        db.refresh(record)
        db.expunge(record)

        return record


def test_successful_login_creates_audit_log():
    assert register_user().status_code == 201

    response = login_user()

    assert response.status_code == 200

    logs = get_audit_logs(AuditAction.LOGIN_SUCCESS)

    assert len(logs) == 1
    assert logs[0].status == AuditStatus.SUCCESS
    assert logs[0].actor_username == "audituser"


def test_failed_login_creates_audit_log():
    assert register_user().status_code == 201

    response = login_user(password="IncorrectPassword123!")

    assert response.status_code == 401

    logs = get_audit_logs(AuditAction.LOGIN_FAILURE)

    assert len(logs) == 1
    assert logs[0].status == AuditStatus.FAILURE
    assert logs[0].details == {"reason": "invalid_credentials"}


def test_password_change_creates_audit_log():
    assert register_user().status_code == 201
    login_response = login_user()
    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    logs = get_audit_logs(AuditAction.PASSWORD_CHANGE)

    assert len(logs) == 1
    assert logs[0].resource_type == "user"
    assert logs[0].details == {"refresh_sessions_revoked": 1}


def test_role_change_creates_audit_log():
    admin = create_user("auditadmin", UserRole.ADMIN)
    target = create_user("audittarget", UserRole.VIEWER)

    response = client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "fraud_analyst"},
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    logs = get_audit_logs(AuditAction.USER_ROLE_UPDATE)

    assert len(logs) == 1
    assert logs[0].actor_username == admin.username
    assert logs[0].details == {
        "old_role": "viewer",
        "new_role": "fraud_analyst",
        "target_username": target.username,
    }


def test_fraud_score_creates_audit_log(monkeypatch):
    analyst = create_user("auditanalyst", UserRole.FRAUD_ANALYST)
    scoring_result = {
        "model_name": "test-model",
        "fraud_probability": 0.91,
        "fraud_prediction": 1,
        "fraud_threshold": 0.84,
        "risk_band": "high",
        "feature_quality": {
            "expected_feature_count": 0,
            "missing_features_count": 0,
            "extra_features_count": 0,
            "missing_features_preview": [],
            "extra_features_preview": [],
        },
    }
    monkeypatch.setattr(
        "backend.app.api.fraud.score_transaction",
        lambda _: scoring_result,
    )

    response = client.post(
        "/api/v1/fraud/score",
        json={
            "transaction_id": "audit-transaction-001",
            "features": {"confidential": "not-audited"},
        },
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200

    logs = get_audit_logs(AuditAction.FRAUD_SCORE)

    assert len(logs) == 1
    assert logs[0].resource_id == "audit-transaction-001"
    assert "confidential" not in json.dumps(logs[0].details)


def test_case_creation_creates_audit_log():
    analyst = create_user("caseanalyst", UserRole.FRAUD_ANALYST)
    score_record = create_fraud_score_record()

    response = client.post(
        "/api/v1/fraud/cases",
        json={
            "fraud_score_record_id": score_record.id,
            "case_status": "open",
            "analyst_decision": "pending",
            "analyst_notes": "confidential case note",
        },
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200

    logs = get_audit_logs(AuditAction.CASE_CREATE)

    assert len(logs) == 1
    assert logs[0].details == {
        "case_status": "open",
        "priority": "medium",
        "analyst_decision": "pending",
    }
    assert "confidential case note" not in json.dumps(logs[0].details)


def test_admin_can_read_audit_logs():
    admin = create_user("auditreaderadmin", UserRole.ADMIN)

    with TestingSessionLocal() as db:
        create_audit_log(
            db=db,
            action=AuditAction.LOGIN_SUCCESS,
            status=AuditStatus.SUCCESS,
            user=admin,
        )

    response = client.get(
        "/api/v1/audit-logs",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_auditor_can_read_audit_logs():
    auditor = create_user("auditreaderauditor", UserRole.AUDITOR)

    response = client.get(
        "/api/v1/audit-logs",
        headers=auth_headers(auditor),
    )

    assert response.status_code == 200


def test_fraud_analyst_cannot_read_audit_logs():
    analyst = create_user("auditreaderanalyst", UserRole.FRAUD_ANALYST)

    response = client.get(
        "/api/v1/audit-logs",
        headers=auth_headers(analyst),
    )

    assert response.status_code == 403


def test_audit_log_filters_work():
    admin = create_user("filteradmin", UserRole.ADMIN)

    with TestingSessionLocal() as db:
        create_audit_log(
            db=db,
            action=AuditAction.LOGIN_SUCCESS,
            status=AuditStatus.SUCCESS,
            user=admin,
            resource_type="session",
        )
        create_audit_log(
            db=db,
            action=AuditAction.PASSWORD_CHANGE,
            status=AuditStatus.SUCCESS,
            user=admin,
            resource_type="user",
        )

    response = client.get(
        "/api/v1/audit-logs",
        params={
            "action": AuditAction.PASSWORD_CHANGE.value,
            "status": AuditStatus.SUCCESS.value,
            "actor_username": admin.username,
            "resource_type": "user",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["action"] == (
        AuditAction.PASSWORD_CHANGE.value
    )


def test_audit_log_pagination_works():
    admin = create_user("paginationadmin", UserRole.ADMIN)

    with TestingSessionLocal() as db:
        for action in (
            AuditAction.LOGIN_SUCCESS,
            AuditAction.LOGOUT,
            AuditAction.PASSWORD_CHANGE,
        ):
            create_audit_log(
                db=db,
                action=action,
                status=AuditStatus.SUCCESS,
                user=admin,
            )

    response = client.get(
        "/api/v1/audit-logs",
        params={"limit": 1, "offset": 1},
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["items"]) == 1


def test_audit_logs_do_not_store_passwords_or_tokens():
    assert register_user().status_code == 201
    login_response = login_user()
    login_data = login_response.json()
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    change_response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert change_response.status_code == 200

    logs = get_audit_logs()
    serialized_logs = json.dumps(
        [
            {
                "actor_username": log.actor_username,
                "action": log.action,
                "status": log.status,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "details": log.details,
            }
            for log in logs
        ],
        default=str,
    )

    assert PASSWORD not in serialized_logs
    assert NEW_PASSWORD not in serialized_logs
    assert access_token not in serialized_logs
    assert refresh_token not in serialized_logs
