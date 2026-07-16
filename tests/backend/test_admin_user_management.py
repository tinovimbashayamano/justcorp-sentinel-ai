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


def create_user(
    username: str,
    role: UserRole,
    is_active: bool = True,
) -> User:
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
            is_active=is_active,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)

        return user
    finally:
        db.close()


def create_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def test_admin_can_list_users():
    admin = create_user("adminlist", UserRole.ADMIN)
    create_user("viewerlist", UserRole.VIEWER)

    response = client.get(
        "/api/v1/admin/users",
        headers=create_headers(admin),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_non_admin_cannot_list_users():
    analyst = create_user(
        "analystdenied",
        UserRole.FRAUD_ANALYST,
    )

    response = client.get(
        "/api/v1/admin/users",
        headers=create_headers(analyst),
    )

    assert response.status_code == 403


def test_admin_can_change_user_role():
    admin = create_user("adminrole", UserRole.ADMIN)
    viewer = create_user("viewerrole", UserRole.VIEWER)

    response = client.patch(
        f"/api/v1/admin/users/{viewer.id}/role",
        json={
            "role": "fraud_analyst",
        },
        headers=create_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "fraud_analyst"


def test_admin_can_deactivate_user():
    admin = create_user("adminstatus", UserRole.ADMIN)
    viewer = create_user("viewerstatus", UserRole.VIEWER)

    response = client.patch(
        f"/api/v1/admin/users/{viewer.id}/status",
        json={
            "is_active": False,
        },
        headers=create_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_admin_cannot_deactivate_self():
    admin = create_user("adminselfstatus", UserRole.ADMIN)

    response = client.patch(
        f"/api/v1/admin/users/{admin.id}/status",
        json={
            "is_active": False,
        },
        headers=create_headers(admin),
    )

    assert response.status_code == 400


def test_admin_cannot_remove_own_admin_role():
    admin = create_user("adminselfrole", UserRole.ADMIN)

    response = client.patch(
        f"/api/v1/admin/users/{admin.id}/role",
        json={
            "role": "viewer",
        },
        headers=create_headers(admin),
    )

    assert response.status_code == 400


def test_unauthenticated_user_cannot_access_admin_api():
    response = client.get("/api/v1/admin/users")

    assert response.status_code == 401
