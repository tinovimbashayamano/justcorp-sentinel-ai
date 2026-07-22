from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from backend.app.schemas.investigation_task import (
    InvestigationTaskCancellation,
    InvestigationTaskCompletion,
    InvestigationTaskCreate,
    InvestigationTaskStatusUpdate,
    InvestigationTaskUpdate,
)


def test_create_task_trims_title() -> None:
    payload = InvestigationTaskCreate(
        title="   Review customer profile   ",
    )

    assert payload.title == "Review customer profile"


def test_create_task_rejects_invalid_priority() -> None:
    with pytest.raises(ValidationError):
        InvestigationTaskCreate(
            title="Review customer profile",
            priority="urgent",
        )


def test_create_task_rejects_naive_due_date() -> None:
    with pytest.raises(ValidationError):
        InvestigationTaskCreate(
            title="Review customer profile",
            due_at=datetime.now() + timedelta(days=1),
        )


def test_create_task_accepts_future_aware_due_date() -> None:
    payload = InvestigationTaskCreate(
        title="Review customer profile",
        due_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    assert payload.due_at is not None
    assert payload.due_at.tzinfo is not None


def test_update_requires_at_least_one_change() -> None:
    with pytest.raises(ValidationError):
        InvestigationTaskUpdate()


def test_status_update_rejects_completed() -> None:
    with pytest.raises(ValidationError):
        InvestigationTaskStatusUpdate(
            status="completed",
        )


def test_status_update_rejects_cancelled() -> None:
    with pytest.raises(ValidationError):
        InvestigationTaskStatusUpdate(
            status="cancelled",
        )


def test_completion_requires_note() -> None:
    with pytest.raises(ValidationError):
        InvestigationTaskCompletion(
            completion_note=" ",
        )


def test_cancellation_requires_reason() -> None:
    with pytest.raises(ValidationError):
        InvestigationTaskCancellation(
            cancellation_reason=" ",
        )
