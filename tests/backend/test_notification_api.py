"""Integration tests for the notification API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.security import create_access_token
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.models.user import User, UserRole
from backend.app.services.notification_service import NotificationService


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
    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )
    return {"Authorization": f"Bearer {token}"}


def create_notification(
    recipient: User,
    *,
    title: str,
    deduplication_key: str,
) -> int:
    with TestingSessionLocal() as db:
        notification = NotificationService(db).create_notification(
            recipient_user_id=recipient.id,
            notification_type="system",
            title=title,
            message=f"{title} body",
            deduplication_key=deduplication_key,
        )
        return notification.id


def test_list_notifications_returns_authenticated_users_records():
    first_user = create_user("listanalyst", UserRole.FRAUD_ANALYST)
    second_user = create_user("listother", UserRole.FRAUD_ANALYST)
    create_notification(
        first_user,
        title="Owned notification",
        deduplication_key="list-owned",
    )
    create_notification(
        second_user,
        title="Other notification",
        deduplication_key="list-other",
    )

    response = client.get(
        "/api/v1/notifications",
        headers=auth_headers(first_user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Owned notification"
    assert body["items"][0]["recipient_user_id"] == first_user.id


def test_user_cannot_read_another_users_notification():
    owner = create_user("notificationowner", UserRole.FRAUD_ANALYST)
    other_user = create_user("notificationother", UserRole.FRAUD_ANALYST)
    notification_id = create_notification(
        owner,
        title="Private notification",
        deduplication_key="private-notification",
    )

    response = client.get(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers(other_user),
    )

    assert response.status_code == 404


def test_mark_notification_as_read():
    user = create_user("readanalyst", UserRole.FRAUD_ANALYST)
    notification_id = create_notification(
        user,
        title="Read notification",
        deduplication_key="read-notification",
    )

    response = client.patch(
        f"/api/v1/notifications/{notification_id}/read",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["is_read"] is True
    assert response.json()["read_at"] is not None


def test_delete_and_restore_notification():
    user = create_user("restoreanalyst", UserRole.FRAUD_ANALYST)
    notification_id = create_notification(
        user,
        title="Restore notification",
        deduplication_key="restore-notification",
    )

    deleted = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers(user),
    )
    assert deleted.status_code == 200
    assert deleted.json()["is_deleted"] is True

    restored = client.post(
        f"/api/v1/notifications/{notification_id}/restore",
        headers=auth_headers(user),
    )
    assert restored.status_code == 200
    assert restored.json()["is_deleted"] is False


def test_get_unread_count():
    user = create_user("unreadanalyst", UserRole.FRAUD_ANALYST)
    create_notification(
        user,
        title="Unread notification",
        deduplication_key="unread-notification",
    )

    response = client.get(
        "/api/v1/notifications/unread-count",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json() == {"unread_count": 1}


def test_get_notification_statistics():
    user = create_user("statisticsanalyst", UserRole.FRAUD_ANALYST)
    create_notification(
        user,
        title="Statistics notification",
        deduplication_key="statistics-notification",
    )

    response = client.get(
        "/api/v1/notifications/statistics",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["unread"] == 1
    assert body["today"] == 1


def test_admin_can_create_notification():
    admin = create_user("notificationadmin", UserRole.ADMIN)
    recipient = create_user("adminrecipient", UserRole.FRAUD_ANALYST)

    response = client.post(
        "/api/v1/notifications/admin",
        json={
            "recipient_user_id": recipient.id,
            "title": "Administrative notification",
            "message": "Created by an administrator.",
            "deduplication_key": "admin-created",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["recipient_user_id"] == recipient.id
    assert body["actor_user_id"] == admin.id
    assert body["status"] == "delivered"


def test_non_admin_cannot_create_administrative_notification():
    analyst = create_user("nonadminanalyst", UserRole.FRAUD_ANALYST)
    recipient = create_user("nonadminrecipient", UserRole.FRAUD_ANALYST)

    response = client.post(
        "/api/v1/notifications/admin",
        json={
            "recipient_user_id": recipient.id,
            "title": "Denied notification",
            "message": "This should not be created.",
        },
        headers=auth_headers(analyst),
    )

    assert response.status_code == 403


def test_admin_can_process_email_retry_queue():
    admin = create_user("retryadmin", UserRole.ADMIN)

    response = client.post(
        "/api/v1/notifications/admin/process-email-retries?limit=10",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json() == {
        "examined": 0,
        "delivered": 0,
        "failed": 0,
        "skipped": 0,
    }
