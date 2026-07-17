import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import hash_refresh_token
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User


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
    "username": "refreshuser",
    "email": "refresh@example.com",
    "password": "SecurePassword123!",
    "full_name": "Refresh Token User",
}


def register_test_user():
    return client.post(
        "/api/v1/auth/register",
        json=VALID_REGISTRATION_PAYLOAD,
    )


def login_test_user():
    return client.post(
        "/api/v1/auth/login",
        data={
            "username": VALID_REGISTRATION_PAYLOAD["username"],
            "password": VALID_REGISTRATION_PAYLOAD["password"],
        },
    )


def register_and_login():
    registration_response = register_test_user()
    assert registration_response.status_code == 201

    login_response = login_test_user()
    assert login_response.status_code == 200

    return registration_response.json(), login_response.json()


def test_login_returns_token_pair():
    register_test_user()

    response = login_test_user()

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_refresh_returns_new_token_pair():
    _, login_data = register_and_login()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["refresh_token"] != login_data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_old_refresh_token_is_rejected_after_rotation():
    _, login_data = register_and_login()
    old_refresh_token = login_data["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert refresh_response.status_code == 200

    reused_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert reused_response.status_code == 401
    assert reused_response.json()["detail"] == (
        "Refresh token has been revoked."
    )


def test_invalid_refresh_token_is_rejected():
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "x" * 64},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is invalid."


def test_logout_revokes_refresh_token():
    _, login_data = register_and_login()
    refresh_token = login_data["refresh_token"]

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful."}

    with TestingSessionLocal() as db:
        token_record = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash
                == hash_refresh_token(refresh_token)
            )
            .one()
        )

        assert token_record.is_revoked is True
        assert token_record.revoked_at is not None


def test_revoked_token_cannot_refresh():
    _, login_data = register_and_login()
    refresh_token = login_data["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 200

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == (
        "Refresh token has been revoked."
    )


def test_inactive_user_cannot_refresh():
    registration_data, login_data = register_and_login()

    with TestingSessionLocal() as db:
        user = db.get(User, registration_data["id"])
        assert user is not None

        user.is_active = False
        db.commit()

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Refresh token user is unavailable."
    )
