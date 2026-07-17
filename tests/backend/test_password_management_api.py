import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.refresh_token import RefreshToken


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


CURRENT_PASSWORD = "SecurePassword123!"
NEW_PASSWORD = "NewSecurePassword456!"

VALID_REGISTRATION_PAYLOAD = {
    "username": "passworduser",
    "email": "passworduser@example.com",
    "password": CURRENT_PASSWORD,
    "full_name": "Password User",
}


def register_test_user():
    response = client.post(
        "/api/v1/auth/register",
        json=VALID_REGISTRATION_PAYLOAD,
    )

    assert response.status_code == 201

    return response


def login_test_user(password: str = CURRENT_PASSWORD):
    return client.post(
        "/api/v1/auth/login",
        data={
            "username": VALID_REGISTRATION_PAYLOAD["username"],
            "password": password,
        },
    )


def register_and_login():
    register_test_user()

    response = login_test_user()
    assert response.status_code == 200

    return response.json()


def change_password(
    access_token: str,
    current_password: str = CURRENT_PASSWORD,
    new_password: str = NEW_PASSWORD,
):
    return client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": current_password,
            "new_password": new_password,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )


def test_change_password_requires_authentication():
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": CURRENT_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 401


def test_change_password_rejects_wrong_current_password():
    login_data = register_and_login()

    response = change_password(
        access_token=login_data["access_token"],
        current_password="IncorrectPassword123!",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect."


def test_change_password_rejects_same_password():
    login_data = register_and_login()

    response = change_password(
        access_token=login_data["access_token"],
        new_password=CURRENT_PASSWORD,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "New password must be different from the current password."
    )


def test_change_password_rejects_weak_new_password():
    login_data = register_and_login()

    response = change_password(
        access_token=login_data["access_token"],
        new_password="weakpassword",
    )

    assert response.status_code == 422


def test_change_password_succeeds():
    login_data = register_and_login()

    response = change_password(
        access_token=login_data["access_token"],
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": (
            "Password changed successfully. "
            "1 refresh session(s) revoked."
        )
    }


def test_old_password_fails_after_change():
    login_data = register_and_login()

    change_response = change_password(
        access_token=login_data["access_token"],
    )
    assert change_response.status_code == 200

    response = login_test_user(password=CURRENT_PASSWORD)

    assert response.status_code == 401


def test_new_password_works_after_change():
    login_data = register_and_login()

    change_response = change_password(
        access_token=login_data["access_token"],
    )
    assert change_response.status_code == 200

    response = login_test_user(password=NEW_PASSWORD)

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_password_change_revokes_refresh_tokens():
    login_data = register_and_login()

    change_response = change_password(
        access_token=login_data["access_token"],
    )
    assert change_response.status_code == 200

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_data["refresh_token"]},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Refresh token has been revoked."
    )


def test_logout_all_revokes_every_active_refresh_token():
    first_login_data = register_and_login()

    second_login_response = login_test_user()
    assert second_login_response.status_code == 200
    second_login_data = second_login_response.json()

    response = client.post(
        "/api/v1/auth/logout-all",
        headers={
            "Authorization": (
                f"Bearer {first_login_data['access_token']}"
            ),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "2 refresh session(s) revoked."
    }

    with TestingSessionLocal() as db:
        active_token_count = (
            db.query(RefreshToken)
            .filter(RefreshToken.is_revoked.is_(False))
            .count()
        )

        assert active_token_count == 0

    for refresh_token in (
        first_login_data["refresh_token"],
        second_login_data["refresh_token"],
    ):
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert refresh_response.status_code == 401
