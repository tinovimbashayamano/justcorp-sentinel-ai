"""Regression tests for notification model registration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_notification_can_be_instantiated_after_direct_import() -> None:
    """A direct model import must resolve User when mappers configure."""

    verification_code = """
from backend.app.models.notification import Notification

notification = Notification(
    recipient_user_id=1,
    actor_user_id=1,
    notification_type="system",
    title="Direct import verification",
    message="Mapper configuration succeeds.",
)

assert notification.recipient_user_id == 1
print("direct_notification_import=passed")
"""

    result = subprocess.run(
        [sys.executable, "-c", verification_code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "direct_notification_import=passed" in result.stdout
