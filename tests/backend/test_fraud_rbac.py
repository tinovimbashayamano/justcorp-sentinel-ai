import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import (
    create_access_token,
    hash_password,
)
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.user import User, UserRole


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


def create_user_headers(
    username: str,
    role: UserRole,
) -> dict[str, str]:
    db = TestingSessionLocal()

    try:
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=f"{username} user",
            hashed_password=hash_password(
                "SecurePassword123!"
            ),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )

        return {
            "Authorization": f"Bearer {token}",
        }
    finally:
        db.close()


def test_viewer_can_access_model_health():
    headers = create_user_headers(
        "viewerhealth",
        UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/fraud/health",
        headers=headers,
    )

    assert response.status_code in [200, 503]


def test_viewer_cannot_score_transaction():
    headers = create_user_headers(
        "viewerscore",
        UserRole.VIEWER,
    )

    response = client.post(
        "/api/v1/fraud/score",
        json={
            "transaction_id": "viewer-test",
            "features": {},
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_viewer_cannot_read_fraud_scores():
    headers = create_user_headers(
        "viewerscores",
        UserRole.VIEWER,
    )

    response = client.get(
        "/api/v1/fraud/scores",
        headers=headers,
    )

    assert response.status_code == 403


def test_auditor_can_read_fraud_scores():
    headers = create_user_headers(
        "auditorread",
        UserRole.AUDITOR,
    )

    response = client.get(
        "/api/v1/fraud/scores",
        headers=headers,
    )

    assert response.status_code == 200


def test_auditor_cannot_score_transaction():
    headers = create_user_headers(
        "auditorscore",
        UserRole.AUDITOR,
    )

    response = client.post(
        "/api/v1/fraud/score",
        json={
            "transaction_id": "auditor-test",
            "features": {},
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_auditor_cannot_create_case():
    headers = create_user_headers(
        "auditorcase",
        UserRole.AUDITOR,
    )

    response = client.post(
        "/api/v1/fraud/cases",
        json={
            "fraud_score_record_id": 1,
            "case_status": "open",
            "analyst_decision": "pending",
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_fraud_analyst_can_score_transaction():
    headers = create_user_headers(
        "analystscore",
        UserRole.FRAUD_ANALYST,
    )

    response = client.post(
        "/api/v1/fraud/score",
        json={
            "transaction_id": "analyst-test",
            "features": {},
        },
        headers=headers,
    )

    assert response.status_code in [200, 503]


def test_admin_can_read_fraud_scores():
    headers = create_user_headers(
        "adminread",
        UserRole.ADMIN,
    )

    response = client.get(
        "/api/v1/fraud/scores",
        headers=headers,
    )

    assert response.status_code == 200
