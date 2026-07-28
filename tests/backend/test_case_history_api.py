import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.case_history import CaseEvent
from backend.app.core.security import create_access_token, hash_password
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.fraud_score import FraudScoreRecord
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


def create_user(
    username: str,
    role: UserRole,
) -> User:
    with TestingSessionLocal() as db:
        user = User(
            username=username,
            email=f"{username}@example.com",
            full_name=f"{username} user",
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
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def create_score_record() -> FraudScoreRecord:
    with TestingSessionLocal() as db:
        record = FraudScoreRecord(
            transaction_id="history-source-001",
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


def create_case(
    username: str = "historyanalyst",
) -> tuple[dict, User]:
    analyst = create_user(username, UserRole.FRAUD_ANALYST)
    score_record = create_score_record()

    response = client.post(
        "/api/v1/fraud/cases",
        json={
            "fraud_score_record_id": score_record.id,
            "case_status": "open",
            "priority": "medium",
            "analyst_decision": "pending",
        },
        headers=auth_headers(analyst),
    )

    assert response.status_code == 200

    return response.json(), analyst


def get_timeline(
    case_id: int,
    user: User,
):
    return client.get(
        f"/api/v1/cases/{case_id}/timeline",
        headers=auth_headers(user),
    )


def update_case(
    case_id: int,
    analyst: User,
    payload: dict,
):
    return client.patch(
        f"/api/v1/fraud/cases/{case_id}",
        json=payload,
        headers=auth_headers(analyst),
    )


def test_case_creation_creates_history():
    case, analyst = create_case()

    response = get_timeline(case["id"], analyst)

    assert response.status_code == 200

    timeline = response.json()

    assert len(timeline) == 1
    assert timeline[0]["actor_username"] == analyst.username
    assert timeline[0]["event_type"] == CaseEvent.CREATED
    assert timeline[0]["details"] == {
        "status": "open",
        "priority": "medium",
    }


def test_status_change_creates_history():
    case, analyst = create_case()

    response = update_case(
        case["id"],
        analyst,
        {"case_status": "investigating"},
    )

    assert response.status_code == 200

    timeline = get_timeline(case["id"], analyst).json()

    assert timeline[-1]["event_type"] == CaseEvent.STATUS_CHANGED
    assert timeline[-1]["details"] == {
        "old": "open",
        "new": "investigating",
    }


@pytest.mark.parametrize(
    "case_status",
    [
        "new",
        "assigned",
        "pending_customer",
        "escalated",
        "resolved",
    ],
)
def test_enterprise_workspace_statuses_are_accepted(case_status):
    case, analyst = create_case(
        username=f"status-{case_status}",
    )

    response = update_case(
        case["id"],
        analyst,
        {"case_status": case_status},
    )

    assert response.status_code == 200
    assert response.json()["case_status"] == case_status


def test_priority_change_creates_history():
    case, analyst = create_case()

    response = update_case(
        case["id"],
        analyst,
        {"priority": "high"},
    )

    assert response.status_code == 200

    timeline = get_timeline(case["id"], analyst).json()

    assert timeline[-1]["event_type"] == CaseEvent.PRIORITY_CHANGED
    assert timeline[-1]["details"] == {
        "old": "medium",
        "new": "high",
    }


def test_assignment_creates_history():
    case, analyst = create_case()

    response = update_case(
        case["id"],
        analyst,
        {"assigned_to": "john.smith"},
    )

    assert response.status_code == 200

    timeline = get_timeline(case["id"], analyst).json()

    assert timeline[-1]["event_type"] == CaseEvent.ASSIGNED
    assert timeline[-1]["details"] == {
        "old": None,
        "assigned_to": "john.smith",
    }


def test_close_case_creates_history():
    case, analyst = create_case()

    response = update_case(
        case["id"],
        analyst,
        {
            "case_status": "closed",
            "closure_reason": "Confirmed Fraud",
        },
    )

    assert response.status_code == 200

    timeline = get_timeline(case["id"], analyst).json()

    assert timeline[-1]["event_type"] == CaseEvent.CLOSED
    assert timeline[-1]["details"] == {
        "old": "open",
        "new": "closed",
        "reason": "Confirmed Fraud",
    }


def test_history_order():
    case, analyst = create_case()

    assert update_case(
        case["id"],
        analyst,
        {"case_status": "investigating"},
    ).status_code == 200
    assert update_case(
        case["id"],
        analyst,
        {"priority": "critical"},
    ).status_code == 200

    timeline = get_timeline(case["id"], analyst).json()

    assert [entry["event_type"] for entry in timeline] == [
        CaseEvent.CREATED,
        CaseEvent.STATUS_CHANGED,
        CaseEvent.PRIORITY_CHANGED,
    ]
    assert [entry["id"] for entry in timeline] == sorted(
        entry["id"] for entry in timeline
    )


def test_admin_can_read_history():
    case, _ = create_case()
    admin = create_user("historyadmin", UserRole.ADMIN)

    response = get_timeline(case["id"], admin)

    assert response.status_code == 200


def test_analyst_can_read_history():
    case, analyst = create_case()

    response = get_timeline(case["id"], analyst)

    assert response.status_code == 200


def test_auditor_can_read_history():
    case, _ = create_case()
    auditor = create_user("historyauditor", UserRole.AUDITOR)

    response = get_timeline(case["id"], auditor)

    assert response.status_code == 200


def test_viewer_cannot_read_history():
    case, _ = create_case()
    viewer = create_user("historyviewer", UserRole.VIEWER)

    response = get_timeline(case["id"], viewer)

    assert response.status_code == 403
