import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.security import create_access_token


def create_test_access_token(
    user_id: int,
    role: str = "viewer",
) -> str:
    return create_access_token(
        subject=str(user_id),
        role=role,
    )
