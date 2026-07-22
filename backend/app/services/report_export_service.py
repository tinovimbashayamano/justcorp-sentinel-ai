"""JSON, CSV and PDF export service for fraud-case reports."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.app.core.reporting import (
    REPORT_FILE_EXTENSIONS,
    REPORT_MIME_TYPES,
    REPORT_STORAGE_DIRECTORY,
    ReportFormat,
    ensure_report_storage_directory,
    validate_report_type_format_combination,
)


class ReportExportError(RuntimeError):
    """Base report export error."""


class UnsupportedExportFormatError(ReportExportError):
    """Raised when an export format is unsupported."""


class InvalidReportPayloadError(ReportExportError):
    """Raised when report data cannot be rendered safely."""


class ReportStorageError(ReportExportError):
    """Raised when a report cannot be written to storage."""


@dataclass(frozen=True, slots=True)
class ExportedReportFile:
    """Metadata returned after a report file has been generated."""

    stored_filename: str
    storage_path: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str


class ReportExportService:
    """Render normalized report data as JSON, CSV or PDF."""

    MAX_FILENAME_LENGTH = 180

    def __init__(self, storage_directory: Path | None = None) -> None:
        self.storage_directory = storage_directory or REPORT_STORAGE_DIRECTORY

    def export(
        self,
        *,
        report_id: int,
        case_id: int,
        report_type: str,
        export_format: str,
        title: str,
        data: Mapping[str, Any],
    ) -> ExportedReportFile:
        """Generate a report file and return persistent file metadata."""

        validate_report_type_format_combination(
            report_type=report_type,
            export_format=export_format,
        )

        if not isinstance(data, Mapping):
            raise InvalidReportPayloadError("Report data must be a mapping.")

        storage_directory = self._ensure_storage_directory()
        extension = REPORT_FILE_EXTENSIONS.get(export_format)
        mime_type = REPORT_MIME_TYPES.get(export_format)

        if extension is None or mime_type is None:
            raise UnsupportedExportFormatError(
                f"Unsupported export format: {export_format}"
            )

        stored_filename = self._build_filename(
            report_id=report_id,
            case_id=case_id,
            report_type=report_type,
            extension=extension,
        )
        destination = self._safe_destination(
            storage_directory=storage_directory,
            filename=stored_filename,
        )

        try:
            content = self._render(
                export_format=export_format,
                title=title,
                report_type=report_type,
                data=data,
            )
            self._write_atomically(destination=destination, content=content)
        except ReportExportError:
            raise
        except OSError as exc:
            raise ReportStorageError(
                "The generated report could not be written to storage."
            ) from exc

        file_size = destination.stat().st_size
        digest = self._sha256_file(destination)

        return ExportedReportFile(
            stored_filename=stored_filename,
            storage_path=str(destination.resolve()),
            mime_type=mime_type,
            file_size_bytes=file_size,
            sha256_hash=digest,
        )

    def delete_file(self, storage_path: str | None) -> bool:
        """Delete a generated report file if it exists within report storage."""

        if not storage_path:
            return False

        report_root = self._ensure_storage_directory().resolve()
        candidate = Path(storage_path).resolve()

        try:
            candidate.relative_to(report_root)
        except ValueError as exc:
            raise ReportStorageError(
                "Refusing to delete a file outside report storage."
            ) from exc

        if not candidate.exists():
            return False
        if not candidate.is_file():
            raise ReportStorageError(
                "The report storage path does not reference a file."
            )

        candidate.unlink()
        return True

    def verify_file(
        self,
        *,
        storage_path: str,
        expected_size: int,
        expected_sha256: str,
    ) -> tuple[bool, bool, bool]:
        """Return existence, size-match and hash-match integrity results."""

        report_root = self._ensure_storage_directory().resolve()
        candidate = Path(storage_path).resolve()

        try:
            candidate.relative_to(report_root)
        except ValueError:
            return False, False, False

        if not candidate.exists() or not candidate.is_file():
            return False, False, False

        size_matches = candidate.stat().st_size == expected_size
        hash_matches = (
            self._sha256_file(candidate).lower() == expected_sha256.lower()
        )
        return True, size_matches, hash_matches

    def _render(
        self,
        *,
        export_format: str,
        title: str,
        report_type: str,
        data: Mapping[str, Any],
    ) -> bytes:
        if export_format == ReportFormat.JSON.value:
            return self._render_json(data)
        if export_format == ReportFormat.CSV.value:
            return self._render_csv(report_type=report_type, data=data)
        if export_format == ReportFormat.PDF.value:
            return self._render_pdf(title=title, data=data)
        raise UnsupportedExportFormatError(
            f"Unsupported export format: {export_format}"
        )

    def _render_json(self, data: Mapping[str, Any]) -> bytes:
        try:
            serialized = json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
                sort_keys=False,
                default=self._json_default,
            )
        except (TypeError, ValueError) as exc:
            raise InvalidReportPayloadError(
                "Report data could not be serialized as JSON."
            ) from exc
        return serialized.encode("utf-8")

    def _render_csv(
        self,
        *,
        report_type: str,
        data: Mapping[str, Any],
    ) -> bytes:
        rows = self._extract_csv_rows(report_type=report_type, data=data)
        if not rows:
            rows = [{"message": "No report records available."}]

        flattened_rows = [self._flatten_mapping(row) for row in rows]
        fieldnames: list[str] = []
        for row in flattened_rows:
            for field in row:
                if field not in fieldnames:
                    fieldnames.append(field)

        output = io.StringIO(newline="")
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in flattened_rows:
            writer.writerow(
                {key: self._csv_value(row.get(key)) for key in fieldnames}
            )
        return output.getvalue().encode("utf-8-sig")

    def _render_pdf(
        self,
        *,
        title: str,
        data: Mapping[str, Any],
    ) -> bytes:
        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=title,
            author="JustCorp Sentinel AI",
            subject="Fraud investigation report",
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=18,
            leading=22,
            spaceAfter=10,
        )
        section_style = ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading2"],
            alignment=TA_LEFT,
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
        )
        small_style = ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontSize=7,
            leading=9,
        )
        story: list[Any] = [
            Paragraph(self._escape_pdf_text(title), title_style),
            Paragraph("Generated by JustCorp Sentinel AI", body_style),
            Spacer(1, 8),
        ]

        for section_name, section_value in data.items():
            story.append(
                Paragraph(self._humanize(section_name), section_style)
            )
            story.extend(
                self._pdf_elements_for_value(
                    value=section_value,
                    body_style=body_style,
                    small_style=small_style,
                )
            )
            story.append(Spacer(1, 6))

        document.build(
            story,
            onFirstPage=self._draw_page_footer,
            onLaterPages=self._draw_page_footer,
        )
        return buffer.getvalue()

    def _pdf_elements_for_value(
        self,
        *,
        value: Any,
        body_style: ParagraphStyle,
        small_style: ParagraphStyle,
    ) -> list[Any]:
        if isinstance(value, Mapping):
            rows = [
                [
                    Paragraph(
                        self._escape_pdf_text(self._humanize(str(key))),
                        small_style,
                    ),
                    Paragraph(
                        self._escape_pdf_text(self._display_value(item)),
                        small_style,
                    ),
                ]
                for key, item in value.items()
            ]
            table = Table(
                rows or [["No data", ""]],
                colWidths=[52 * mm, 112 * mm],
                repeatRows=0,
            )
            table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        (
                            "BACKGROUND",
                            (0, 0),
                            (0, -1),
                            colors.HexColor("#E9EEF5"),
                        ),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            return [table]

        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes, bytearray),
        ):
            if not value:
                return [Paragraph("No records available.", body_style)]
            elements: list[Any] = []
            for index, item in enumerate(value, start=1):
                elements.append(Paragraph(f"Record {index}", body_style))
                elements.extend(
                    self._pdf_elements_for_value(
                        value=item,
                        body_style=body_style,
                        small_style=small_style,
                    )
                )
                elements.append(Spacer(1, 5))
            return elements

        return [
            Paragraph(
                self._escape_pdf_text(self._display_value(value)),
                body_style,
            )
        ]

    def _extract_csv_rows(
        self,
        *,
        report_type: str,
        data: Mapping[str, Any],
    ) -> list[Mapping[str, Any]]:
        section_candidates = {
            "case_summary": ("case_summary",),
            "investigation_timeline": ("timeline",),
            "task_summary": ("tasks",),
            "evidence_inventory": ("evidence",),
            "audit_summary": ("case_history", "audit_logs"),
        }
        rows: list[Mapping[str, Any]] = []
        for section in section_candidates.get(report_type, ()):
            value = data.get(section)
            if isinstance(value, Mapping):
                rows.append(value)
            elif isinstance(value, Sequence) and not isinstance(
                value,
                (str, bytes, bytearray),
            ):
                rows.extend(item for item in value if isinstance(item, Mapping))

        if rows:
            return rows
        for value in data.values():
            if isinstance(value, Mapping):
                rows.append(value)
                break
        return rows

    def _build_filename(
        self,
        *,
        report_id: int,
        case_id: int,
        report_type: str,
        extension: str,
    ) -> str:
        safe_type = self._slugify(report_type)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = (
            f"case_{case_id}_report_{report_id}_"
            f"{safe_type}_{timestamp}{extension}"
        )
        return filename[: self.MAX_FILENAME_LENGTH]

    def _safe_destination(
        self,
        *,
        storage_directory: Path,
        filename: str,
    ) -> Path:
        root = storage_directory.resolve()
        destination = (root / filename).resolve()
        try:
            destination.relative_to(root)
        except ValueError as exc:
            raise ReportStorageError(
                "Generated report path escaped the storage directory."
            ) from exc
        return destination

    def _ensure_storage_directory(self) -> Path:
        try:
            if self.storage_directory == REPORT_STORAGE_DIRECTORY:
                directory = ensure_report_storage_directory()
            else:
                self.storage_directory.mkdir(parents=True, exist_ok=True)
                directory = self.storage_directory
            return directory.resolve()
        except OSError as exc:
            raise ReportStorageError(
                "Report storage directory is unavailable."
            ) from exc

    @staticmethod
    def _write_atomically(*, destination: Path, content: bytes) -> None:
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            temporary.write_bytes(content)
            temporary.replace(destination)
        finally:
            if temporary.exists():
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @classmethod
    def _flatten_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        prefix: str = "",
    ) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, item in value.items():
            field_name = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(item, Mapping):
                output.update(cls._flatten_mapping(item, prefix=field_name))
            else:
                output[field_name] = item
        return output

    @staticmethod
    def _csv_value(value: Any) -> str | int | float:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, (Mapping, list, tuple, set)):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=ReportExportService._json_default,
            )
        return str(value)

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, set):
            return sorted(value)
        raise TypeError(
            f"Object of type {type(value).__name__} is not JSON serializable."
        )

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            value.strip().lower(),
        )
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        return normalized or "report"

    @staticmethod
    def _humanize(value: str) -> str:
        return value.replace("_", " ").strip().title()

    @classmethod
    def _display_value(cls, value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, Mapping):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=cls._json_default,
            )
        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes, bytearray),
        ):
            return json.dumps(
                value,
                ensure_ascii=False,
                default=cls._json_default,
            )
        return str(value)

    @staticmethod
    def _escape_pdf_text(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _draw_page_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(
            18 * mm,
            10 * mm,
            "JustCorp Sentinel AI — Confidential Fraud Investigation Report",
        )
        canvas.drawRightString(
            A4[0] - 18 * mm,
            10 * mm,
            f"Page {document.page}",
        )
        canvas.restoreState()
