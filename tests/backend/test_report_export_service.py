import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from backend.app.services.report_export_service import (
    InvalidReportPayloadError,
    ReportExportService,
    ReportStorageError,
)


PAYLOAD = {
    "metadata": {"case_id": 1, "report_type": "case_summary"},
    "case_summary": {
        "id": 1,
        "case_status": "under_review",
        "priority": "high",
    },
}


@pytest.mark.parametrize(
    ("export_format", "expected_prefix"),
    [
        ("json", b"{"),
        ("csv", b"\xef\xbb\xbf"),
        ("pdf", b"%PDF"),
    ],
)
def test_export_formats_include_integrity_metadata(
    tmp_path: Path,
    export_format: str,
    expected_prefix: bytes,
):
    service = ReportExportService(tmp_path)
    exported = service.export(
        report_id=4,
        case_id=7,
        report_type="case_summary",
        export_format=export_format,
        title="Case Summary",
        data=PAYLOAD,
    )
    content = Path(exported.storage_path).read_bytes()

    assert content.startswith(expected_prefix)
    assert exported.file_size_bytes == len(content)
    assert exported.sha256_hash == hashlib.sha256(content).hexdigest()
    assert service.verify_file(
        storage_path=exported.storage_path,
        expected_size=exported.file_size_bytes,
        expected_sha256=exported.sha256_hash,
    ) == (True, True, True)


def test_json_and_csv_contain_expected_report_values(tmp_path: Path):
    service = ReportExportService(tmp_path)
    json_file = service.export(
        report_id=1,
        case_id=1,
        report_type="case_summary",
        export_format="json",
        title="Summary",
        data=PAYLOAD,
    )
    csv_file = service.export(
        report_id=2,
        case_id=1,
        report_type="case_summary",
        export_format="csv",
        title="Summary",
        data=PAYLOAD,
    )

    assert json.loads(Path(json_file.storage_path).read_text("utf-8")) == PAYLOAD
    csv_text = Path(csv_file.storage_path).read_text("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert rows[0]["case_status"] == "under_review"
    assert rows[0]["priority"] == "high"


def test_verify_file_detects_tampering(tmp_path: Path):
    service = ReportExportService(tmp_path)
    exported = service.export(
        report_id=1,
        case_id=1,
        report_type="case_summary",
        export_format="json",
        title="Summary",
        data=PAYLOAD,
    )
    Path(exported.storage_path).write_bytes(b"tampered")

    exists, size_matches, hash_matches = service.verify_file(
        storage_path=exported.storage_path,
        expected_size=exported.file_size_bytes,
        expected_sha256=exported.sha256_hash,
    )
    assert exists is True
    assert not size_matches or not hash_matches


def test_export_hash_matches_generated_file(tmp_path: Path):
    service = ReportExportService(tmp_path)
    exported = service.export(
        report_id=12,
        case_id=1,
        report_type="case_summary",
        export_format="json",
        title="Summary",
        data=PAYLOAD,
    )
    content = Path(exported.storage_path).read_bytes()

    assert exported.sha256_hash == hashlib.sha256(content).hexdigest()


def test_verify_file_detects_valid_file(tmp_path: Path):
    service = ReportExportService(tmp_path)
    exported = service.export(
        report_id=13,
        case_id=1,
        report_type="case_summary",
        export_format="json",
        title="Summary",
        data=PAYLOAD,
    )

    assert service.verify_file(
        storage_path=exported.storage_path,
        expected_size=exported.file_size_bytes,
        expected_sha256=exported.sha256_hash,
    ) == (True, True, True)


def test_delete_file_is_storage_scoped(tmp_path: Path):
    service = ReportExportService(tmp_path / "reports")
    exported = service.export(
        report_id=1,
        case_id=1,
        report_type="case_summary",
        export_format="json",
        title="Summary",
        data=PAYLOAD,
    )
    outside = tmp_path / "outside.json"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(ReportStorageError):
        service.delete_file(str(outside))

    assert service.delete_file(exported.storage_path) is True
    assert service.delete_file(exported.storage_path) is False


def test_non_mapping_payload_is_rejected(tmp_path: Path):
    service = ReportExportService(tmp_path)
    with pytest.raises(InvalidReportPayloadError):
        service.export(
            report_id=1,
            case_id=1,
            report_type="case_summary",
            export_format="json",
            title="Summary",
            data=["invalid"],  # type: ignore[arg-type]
        )
