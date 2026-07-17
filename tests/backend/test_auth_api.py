import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.session import Base, get_db
from backend.app.main import app


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


VALID_REGISTRATION_PAYLOAD = {
    "username": "testanalyst",
    "email": "analyst@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test Analyst",
}


def register_test_user():
    return client.post(
        "/api/v1/auth/register",
        json=VALID_REGISTRATION_PAYLOAD,
    )


def login_test_user(
    username: str = "testanalyst",
    password: str = "SecurePassword123!",
):
    return client.post(
        "/api/v1/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )


def test_register_user():
    response = register_test_user()

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testanalyst"
    assert data["email"] == "analyst@example.com"
    assert data["full_name"] == "Test Analyst"
    assert data["role"] == "viewer"
    assert data["is_active"] is True
    assert "hashed_password" not in data
    assert "password" not in data


def test_duplicate_username_is_rejected():
    first_response = register_test_user()

    assert first_response.status_code == 201

    duplicate_payload = {
        **VALID_REGISTRATION_PAYLOAD,
        "email": "different@example.com",
    }

    duplicate_response = client.post(
        "/api/v1/auth/register",
        json=duplicate_payload,
    )

    assert duplicate_response.status_code == 409


def test_duplicate_email_is_rejected():
    first_response = register_test_user()

    assert first_response.status_code == 201

    duplicate_payload = {
        **VALID_REGISTRATION_PAYLOAD,
        "username": "differentuser",
    }

    duplicate_response = client.post(
        "/api/v1/auth/register",
        json=duplicate_payload,
    )

    assert duplicate_response.status_code == 409


def test_login_with_username():
    register_test_user()

    response = login_test_user()

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in_seconds"] > 0


def test_login_with_email():
    register_test_user()

    response = login_test_user(
        username="analyst@example.com",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_is_rejected():
    register_test_user()

    response = login_test_user(
        password="WrongPassword123!",
    )

    assert response.status_code == 401


def test_me_requires_authentication():
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user():
    register_test_user()
    login_response = login_test_user()

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "testanalyst"
    assert data["email"] == "analyst@example.com"
    assert data["role"] == "viewer"


def test_registration_rejects_weak_password():
    weak_payload = {
        **VALID_REGISTRATION_PAYLOAD,
        "password": "weakpassword",
    }

    response = client.post(
        "/api/v1/auth/register",
        json=weak_payload,
    )

    assert response.status_code == 422
