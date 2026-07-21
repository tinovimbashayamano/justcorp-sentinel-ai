from pathlib import Path


BASE_STORAGE_DIR = Path("storage")

EVIDENCE_STORAGE_DIR = BASE_STORAGE_DIR / "evidence"

EVIDENCE_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)
