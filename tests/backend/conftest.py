"""Shared fixtures for notification subsystem tests."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.session import Base
from backend.app.models.notification import Notification  # noqa: F401
from backend.app.models.user import User, UserRole


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        username="notification-test-user",
        email="notification-test@example.com",
        hashed_password="not-used-by-tests",
        role=UserRole.FRAUD_ANALYST,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
