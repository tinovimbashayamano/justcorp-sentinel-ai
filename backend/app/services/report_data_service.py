"""Data aggregation service for fraud-case reports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import Select, inspect, select
from sqlalchemy.orm import Session

from backend.app.core.reporting import ReportType
from backend.app.models.audit_log import AuditLog
from backend.app.models.case_comment import CaseComment
from backend.app.models.case_evidence import CaseEvidence
from backend.app.models.case_history import CaseHistory
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.investigation_task import InvestigationTask
from backend.app.schemas.report import ReportGenerationOptions


class ReportDataError(RuntimeError):
    """Base error raised while assembling report data."""


class ReportCaseNotFoundError(ReportDataError):
    """Raised when the requested fraud case does not exist."""


class UnsupportedReportTypeError(ReportDataError):
    """Raised when a report type has no supported data builder."""


class ReportDataPermissionError(ReportDataError):
    """Raised when restricted reporting options are not permitted."""


class ReportDataService:
    """Aggregate normalized fraud-case information for report exports."""

    INTERNAL_COMMENT_ROLES = frozenset(
        {
            "admin",
            "fraud_analyst",
            "auditor",
        }
    )

    SENSITIVE_DATA_ROLES = frozenset(
        {
            "admin",
            "fraud_analyst",
            "auditor",
        }
    )

    DETAILED_AUDIT_ROLES = frozenset(
        {
            "admin",
            "auditor",
        }
    )

    SENSITIVE_FIELD_NAMES = frozenset(
        {
            "password",
            "password_hash",
            "hashed_password",
            "access_token",
            "refresh_token",
            "token",
            "secret",
            "api_key",
            "private_key",
            "storage_path",
            "file_path",
            "absolute_path",
        }
    )

    def __init__(self, db: Session) -> None:
        self.db = db

    def build_report_data(
        self,
        *,
        case_id: int,
        report_type: ReportType | str,
        options: ReportGenerationOptions | None = None,
        requester_role: str | None = None,
        requester_user_id: int | None = None,
        requester_username: str | None = None,
    ) -> dict[str, Any]:
        """Build the normalized payload required by a report type."""

        normalized_type = self._enum_value(report_type)
        normalized_options = options or ReportGenerationOptions()
        normalized_role = (requester_role or "").strip().lower()

        self._validate_options(
            options=normalized_options,
            requester_role=normalized_role,
        )

        fraud_case = self._get_case(case_id)
        metadata = self._build_report_metadata(
            fraud_case=fraud_case,
            report_type=normalized_type,
            options=normalized_options,
            requester_user_id=requester_user_id,
            requester_username=requester_username,
        )

        builders = {
            ReportType.CASE_SUMMARY.value: self._build_case_summary_report,
            ReportType.INVESTIGATION_TIMELINE.value: (
                self._build_investigation_timeline_report
            ),
            ReportType.TASK_SUMMARY.value: self._build_task_summary_report,
            ReportType.EVIDENCE_INVENTORY.value: (
                self._build_evidence_inventory_report
            ),
            ReportType.AUDIT_SUMMARY.value: self._build_audit_summary_report,
            ReportType.COMPLETE_CASE.value: self._build_complete_case_report,
        }

        builder = builders.get(normalized_type)
        if builder is None:
            raise UnsupportedReportTypeError(
                f"Unsupported report type: {normalized_type}"
            )

        report_body = builder(
            fraud_case=fraud_case,
            options=normalized_options,
            requester_role=normalized_role,
        )
        return {"metadata": metadata, **report_body}

    def _build_case_summary_report(
        self,
        *,
        fraud_case: FraudCaseReview,
        options: ReportGenerationOptions,
        requester_role: str,
    ) -> dict[str, Any]:
        case_id = self._object_identifier(fraud_case)
        fraud_scores = self._get_case_fraud_scores(fraud_case)
        comments = self._get_case_comments(
            case_id=case_id,
            include_internal=options.include_internal_comments,
            requester_role=requester_role,
        )

        return {
            "case_summary": self._serialize_model(
                fraud_case,
                include_sensitive=options.include_sensitive_data,
            ),
            "fraud_scores": self._serialize_collection(
                fraud_scores,
                include_sensitive=options.include_sensitive_data,
            ),
            "comments": self._serialize_collection(
                comments,
                include_sensitive=options.include_sensitive_data,
            ),
            "statistics": {
                "fraud_score_count": len(fraud_scores),
                "comment_count": len(comments),
            },
        }

    def _build_investigation_timeline_report(
        self,
        *,
        fraud_case: FraudCaseReview,
        options: ReportGenerationOptions,
        requester_role: str,
    ) -> dict[str, Any]:
        case_id = self._object_identifier(fraud_case)
        history_records = self._get_related_records(CaseHistory, case_id=case_id)
        comments = self._get_case_comments(
            case_id=case_id,
            include_internal=options.include_internal_comments,
            requester_role=requester_role,
        )
        tasks = self._get_related_records(InvestigationTask, case_id=case_id)
        timeline = self._merge_timeline_records(
            history_records=history_records,
            comments=comments,
            tasks=tasks,
            include_sensitive=options.include_sensitive_data,
        )

        return {
            "case": self._serialize_model(
                fraud_case,
                include_sensitive=options.include_sensitive_data,
            ),
            "timeline": timeline,
            "statistics": {
                "history_event_count": len(history_records),
                "comment_event_count": len(comments),
                "task_count": len(tasks),
                "timeline_event_count": len(timeline),
            },
        }

    def _build_task_summary_report(
        self,
        *,
        fraud_case: FraudCaseReview,
        options: ReportGenerationOptions,
        requester_role: str,
    ) -> dict[str, Any]:
        del requester_role
        case_id = self._object_identifier(fraud_case)
        tasks = self._get_related_records(InvestigationTask, case_id=case_id)
        serialized_tasks = self._serialize_collection(
            tasks,
            include_sensitive=options.include_sensitive_data,
        )
        status_counts = self._count_by_field(
            serialized_tasks,
            field_candidates=("status", "task_status"),
        )
        priority_counts = self._count_by_field(
            serialized_tasks,
            field_candidates=("priority", "task_priority"),
        )
        assignee_counts = self._count_by_field(
            serialized_tasks,
            field_candidates=(
                "assigned_to_username",
                "assignee_username",
                "assigned_to_user_id",
                "assignee_id",
            ),
        )
        overdue_count = sum(
            1 for task in serialized_tasks if self._is_task_overdue(task)
        )
        completed_count = sum(
            count
            for status, count in status_counts.items()
            if status.lower() in {"completed", "closed", "done"}
        )

        return {
            "case": self._serialize_model(
                fraud_case,
                include_sensitive=options.include_sensitive_data,
            ),
            "tasks": serialized_tasks,
            "statistics": {
                "total_tasks": len(serialized_tasks),
                "completed_tasks": completed_count,
                "overdue_tasks": overdue_count,
                "status_counts": status_counts,
                "priority_counts": priority_counts,
                "assignee_counts": assignee_counts,
            },
        }

    def _build_evidence_inventory_report(
        self,
        *,
        fraud_case: FraudCaseReview,
        options: ReportGenerationOptions,
        requester_role: str,
    ) -> dict[str, Any]:
        del requester_role
        case_id = self._object_identifier(fraud_case)
        evidence_records = self._get_related_records(CaseEvidence, case_id=case_id)
        serialized_evidence = self._serialize_collection(
            evidence_records,
            include_sensitive=options.include_sensitive_data,
        )
        type_counts = self._count_by_field(
            serialized_evidence,
            field_candidates=("evidence_type", "type", "category", "mime_type"),
        )
        status_counts = self._count_by_field(
            serialized_evidence,
            field_candidates=("status", "verification_status", "evidence_status"),
        )
        total_size = sum(
            self._safe_integer(
                self._first_present(
                    evidence,
                    ("file_size_bytes", "size_bytes", "file_size"),
                )
            )
            for evidence in serialized_evidence
        )

        return {
            "case": self._serialize_model(
                fraud_case,
                include_sensitive=options.include_sensitive_data,
            ),
            "evidence": serialized_evidence,
            "statistics": {
                "total_evidence_items": len(serialized_evidence),
                "total_file_size_bytes": total_size,
                "type_counts": type_counts,
                "status_counts": status_counts,
            },
        }

    def _build_audit_summary_report(
        self,
        *,
        fraud_case: FraudCaseReview,
        options: ReportGenerationOptions,
        requester_role: str,
    ) -> dict[str, Any]:
        case_id = self._object_identifier(fraud_case)
        history_records = self._get_related_records(CaseHistory, case_id=case_id)
        audit_logs: Sequence[Any] = []

        if options.include_audit_logs:
            if requester_role not in self.DETAILED_AUDIT_ROLES:
                raise ReportDataPermissionError(
                    "Detailed audit logs require an admin or auditor role."
                )
            audit_logs = self._get_audit_logs(
                case_id=case_id,
                fraud_case=fraud_case,
            )

        serialized_history = self._serialize_collection(
            history_records,
            include_sensitive=options.include_sensitive_data,
        )
        serialized_audit_logs = self._serialize_collection(
            audit_logs,
            include_sensitive=options.include_sensitive_data,
        )
        combined = [*serialized_history, *serialized_audit_logs]

        return {
            "case": self._serialize_model(
                fraud_case,
                include_sensitive=options.include_sensitive_data,
            ),
            "case_history": serialized_history,
            "audit_logs": serialized_audit_logs,
            "statistics": {
                "history_event_count": len(serialized_history),
                "audit_log_count": len(serialized_audit_logs),
                "event_counts": self._count_by_field(
                    combined,
                    field_candidates=(
                        "event_type",
                        "action",
                        "event",
                        "activity_type",
                    ),
                ),
                "actor_counts": self._count_by_field(
                    combined,
                    field_candidates=(
                        "actor_username",
                        "username",
                        "user_id",
                        "actor_user_id",
                    ),
                ),
            },
        }

    def _build_complete_case_report(
        self,
        *,
        fraud_case: FraudCaseReview,
        options: ReportGenerationOptions,
        requester_role: str,
    ) -> dict[str, Any]:
        case_id = self._object_identifier(fraud_case)
        fraud_scores = self._get_case_fraud_scores(fraud_case)
        history_records = self._get_related_records(CaseHistory, case_id=case_id)
        tasks = self._get_related_records(InvestigationTask, case_id=case_id)
        evidence_records = self._get_related_records(CaseEvidence, case_id=case_id)
        comments = self._get_case_comments(
            case_id=case_id,
            include_internal=options.include_internal_comments,
            requester_role=requester_role,
        )
        audit_logs: Sequence[Any] = []

        if options.include_audit_logs:
            if requester_role not in self.DETAILED_AUDIT_ROLES:
                raise ReportDataPermissionError(
                    "Detailed audit logs require an admin or auditor role."
                )
            audit_logs = self._get_audit_logs(
                case_id=case_id,
                fraud_case=fraud_case,
            )

        serialized_scores = self._serialize_collection(
            fraud_scores,
            include_sensitive=options.include_sensitive_data,
        )
        serialized_history = self._serialize_collection(
            history_records,
            include_sensitive=options.include_sensitive_data,
        )
        serialized_tasks = self._serialize_collection(
            tasks,
            include_sensitive=options.include_sensitive_data,
        )
        serialized_evidence = self._serialize_collection(
            evidence_records,
            include_sensitive=options.include_sensitive_data,
        )
        serialized_comments = self._serialize_collection(
            comments,
            include_sensitive=options.include_sensitive_data,
        )
        serialized_audit_logs = self._serialize_collection(
            audit_logs,
            include_sensitive=options.include_sensitive_data,
        )
        timeline = self._merge_timeline_records(
            history_records=history_records,
            comments=comments,
            tasks=tasks,
            include_sensitive=options.include_sensitive_data,
        )

        return {
            "case": self._serialize_model(
                fraud_case,
                include_sensitive=options.include_sensitive_data,
            ),
            "fraud_scores": serialized_scores,
            "timeline": timeline,
            "case_history": serialized_history,
            "tasks": serialized_tasks,
            "evidence": serialized_evidence,
            "comments": serialized_comments,
            "audit_logs": serialized_audit_logs,
            "statistics": {
                "fraud_score_count": len(serialized_scores),
                "history_event_count": len(serialized_history),
                "task_count": len(serialized_tasks),
                "evidence_count": len(serialized_evidence),
                "comment_count": len(serialized_comments),
                "audit_log_count": len(serialized_audit_logs),
                "timeline_event_count": len(timeline),
                "task_status_counts": self._count_by_field(
                    serialized_tasks,
                    field_candidates=("status", "task_status"),
                ),
                "evidence_type_counts": self._count_by_field(
                    serialized_evidence,
                    field_candidates=(
                        "evidence_type",
                        "type",
                        "category",
                        "mime_type",
                    ),
                ),
            },
        }

    def _get_case(self, case_id: int) -> FraudCaseReview:
        fraud_case = self.db.get(FraudCaseReview, case_id)
        if fraud_case is None:
            raise ReportCaseNotFoundError(f"Fraud case {case_id} was not found.")
        return fraud_case

    def _get_case_fraud_scores(
        self,
        fraud_case: FraudCaseReview,
    ) -> Sequence[FraudScoreRecord]:
        """Load the fraud score referenced by this repository's case model."""

        score_id = self._read_attribute(fraud_case, "fraud_score_record_id")
        if score_id is not None:
            score = self.db.get(FraudScoreRecord, score_id)
            return [] if score is None else [score]

        return self._get_related_records(
            FraudScoreRecord,
            case_id=self._object_identifier(fraud_case),
            fallback_transaction_id=self._read_attribute(
                fraud_case,
                "transaction_id",
            ),
            transaction_attribute_candidates=("transaction_id",),
        )

    def _get_related_records(
        self,
        model: type[Any],
        *,
        case_id: int,
        case_attribute_candidates: Sequence[str] = (
            "case_id",
            "fraud_case_id",
            "fraud_case_review_id",
        ),
        fallback_transaction_id: Any = None,
        transaction_attribute_candidates: Sequence[str] = (),
    ) -> Sequence[Any]:
        """Load records associated with a case."""

        case_attribute = self._first_model_attribute(
            model,
            case_attribute_candidates,
        )
        statement: Select[Any] | None = None

        if case_attribute is not None:
            statement = select(model).where(case_attribute == case_id)
        elif fallback_transaction_id is not None and transaction_attribute_candidates:
            transaction_attribute = self._first_model_attribute(
                model,
                transaction_attribute_candidates,
            )
            if transaction_attribute is not None:
                statement = select(model).where(
                    transaction_attribute == fallback_transaction_id
                )

        if statement is None:
            return []

        statement = self._apply_default_ordering(statement, model)
        return list(self.db.scalars(statement).all())

    def _get_case_comments(
        self,
        *,
        case_id: int,
        include_internal: bool,
        requester_role: str,
    ) -> Sequence[CaseComment]:
        comments = list(self._get_related_records(CaseComment, case_id=case_id))

        if not include_internal:
            return [
                comment
                for comment in comments
                if not self._comment_is_internal(comment)
            ]

        if requester_role not in self.INTERNAL_COMMENT_ROLES:
            raise ReportDataPermissionError(
                "Internal comments are not permitted for this role."
            )

        return comments

    def _get_audit_logs(
        self,
        *,
        case_id: int,
        fraud_case: FraudCaseReview,
    ) -> Sequence[AuditLog]:
        case_attribute = self._first_model_attribute(
            AuditLog,
            ("case_id", "fraud_case_id", "fraud_case_review_id"),
        )
        if case_attribute is not None:
            statement = select(AuditLog).where(case_attribute == case_id)
            statement = self._apply_default_ordering(statement, AuditLog)
            return list(self.db.scalars(statement).all())

        resource_id_attribute = self._first_model_attribute(
            AuditLog,
            ("resource_id", "entity_id", "object_id", "record_id"),
        )
        resource_type_attribute = self._first_model_attribute(
            AuditLog,
            ("resource_type", "entity_type", "object_type", "table_name"),
        )

        if resource_id_attribute is not None:
            statement = select(AuditLog).where(
                resource_id_attribute == str(case_id)
            )
            if resource_type_attribute is not None:
                statement = statement.where(
                    resource_type_attribute.in_(
                        (
                            "fraud_case",
                            "fraud_case_review",
                            "fraud_case_reviews",
                            "case",
                        )
                    )
                )
            statement = self._apply_default_ordering(statement, AuditLog)
            return list(self.db.scalars(statement).all())

        transaction_id = self._read_attribute(fraud_case, "transaction_id")
        transaction_attribute = self._first_model_attribute(
            AuditLog,
            ("transaction_id",),
        )
        if transaction_id is not None and transaction_attribute is not None:
            statement = select(AuditLog).where(
                transaction_attribute == transaction_id
            )
            statement = self._apply_default_ordering(statement, AuditLog)
            return list(self.db.scalars(statement).all())

        return []

    def _build_report_metadata(
        self,
        *,
        fraud_case: FraudCaseReview,
        report_type: str,
        options: ReportGenerationOptions,
        requester_user_id: int | None,
        requester_username: str | None,
    ) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "report_type": report_type,
            "case_id": self._object_identifier(fraud_case),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": {
                "user_id": requester_user_id,
                "username": requester_username,
            },
            "options": options.model_dump(mode="json"),
        }

    def _validate_options(
        self,
        *,
        options: ReportGenerationOptions,
        requester_role: str,
    ) -> None:
        if (
            options.include_sensitive_data
            and requester_role not in self.SENSITIVE_DATA_ROLES
        ):
            raise ReportDataPermissionError(
                "Sensitive report data is not permitted for this role."
            )
        if (
            options.include_internal_comments
            and requester_role not in self.INTERNAL_COMMENT_ROLES
        ):
            raise ReportDataPermissionError(
                "Internal comments are not permitted for this role."
            )
        if (
            options.include_audit_logs
            and requester_role not in self.DETAILED_AUDIT_ROLES
        ):
            raise ReportDataPermissionError(
                "Detailed audit logs require an admin or auditor role."
            )

    def _merge_timeline_records(
        self,
        *,
        history_records: Sequence[Any],
        comments: Sequence[Any],
        tasks: Sequence[Any],
        include_sensitive: bool,
    ) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = []

        for source, records in (
            ("case_history", history_records),
            ("case_comment", comments),
            ("investigation_task", tasks),
        ):
            for record in records:
                payload = self._serialize_model(
                    record,
                    include_sensitive=include_sensitive,
                )
                timeline.append(
                    self._timeline_entry(source=source, payload=payload)
                )

        timeline.sort(
            key=lambda item: self._sortable_datetime(item.get("occurred_at"))
        )
        return timeline

    def _timeline_entry(
        self,
        *,
        source: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        occurred_at = self._first_present(
            payload,
            (
                "occurred_at",
                "event_at",
                "created_at",
                "updated_at",
                "completed_at",
                "deleted_at",
            ),
        )
        event_type = self._first_present(
            payload,
            ("event_type", "action", "event", "status", "activity_type"),
        )
        actor = self._first_present(
            payload,
            (
                "actor_username",
                "created_by_username",
                "updated_by_username",
                "username",
                "assigned_to_username",
                "user_id",
            ),
        )
        description = self._first_present(
            payload,
            ("description", "message", "comment", "content", "details", "title"),
        )

        return {
            "source": source,
            "occurred_at": occurred_at,
            "event_type": event_type or source,
            "actor": actor,
            "description": description,
            "data": payload,
        }

    def _serialize_collection(
        self,
        records: Iterable[Any],
        *,
        include_sensitive: bool,
    ) -> list[dict[str, Any]]:
        return [
            self._serialize_model(
                record,
                include_sensitive=include_sensitive,
            )
            for record in records
        ]

    def _serialize_model(
        self,
        instance: Any,
        *,
        include_sensitive: bool,
    ) -> dict[str, Any]:
        """Serialize column values without traversing relationships."""

        mapper = inspect(instance).mapper
        output: dict[str, Any] = {}

        for column_attribute in mapper.column_attrs:
            field_name = column_attribute.key
            if not include_sensitive and self._is_sensitive_field(field_name):
                continue
            try:
                raw_value = getattr(instance, field_name)
            except Exception:
                continue
            output[field_name] = self._normalize_value(raw_value)

        return output

    def _comment_is_internal(self, comment: CaseComment) -> bool:
        for attribute_name in ("is_internal", "internal", "is_private", "private"):
            if hasattr(comment, attribute_name):
                return bool(getattr(comment, attribute_name))

        visibility = self._read_attribute(comment, "visibility")
        if visibility is not None:
            return str(visibility).strip().lower() in {
                "internal",
                "private",
                "restricted",
            }
        return False

    def _is_sensitive_field(self, field_name: str) -> bool:
        normalized = field_name.strip().lower()
        if normalized in self.SENSITIVE_FIELD_NAMES:
            return True
        return any(
            token in normalized
            for token in (
                "password",
                "secret",
                "token",
                "private_key",
                "absolute_path",
            )
        )

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, bytes):
            return value.hex()
        if isinstance(value, Mapping):
            return {
                str(key): ReportDataService._normalize_value(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple, set, frozenset)):
            return [ReportDataService._normalize_value(item) for item in value]
        if isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @staticmethod
    def _first_model_attribute(
        model: type[Any],
        candidates: Sequence[str],
    ) -> Any | None:
        for attribute_name in candidates:
            attribute = getattr(model, attribute_name, None)
            if attribute is not None:
                return attribute
        return None

    @staticmethod
    def _read_attribute(
        instance: Any,
        attribute_name: str,
        default: Any = None,
    ) -> Any:
        return getattr(instance, attribute_name, default)

    @staticmethod
    def _object_identifier(instance: Any) -> int:
        identifier = getattr(instance, "id", None)
        if identifier is None:
            raise ReportDataError("The fraud case has no database identifier.")
        return int(identifier)

    @staticmethod
    def _enum_value(value: Enum | str) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        return str(value)

    @staticmethod
    def _apply_default_ordering(
        statement: Select[Any],
        model: type[Any],
    ) -> Select[Any]:
        for field_name in (
            "created_at",
            "occurred_at",
            "event_at",
            "updated_at",
            "id",
        ):
            attribute = getattr(model, field_name, None)
            if attribute is not None:
                return statement.order_by(attribute.asc())
        return statement

    @staticmethod
    def _first_present(
        record: Mapping[str, Any],
        field_candidates: Sequence[str],
    ) -> Any:
        for field_name in field_candidates:
            value = record.get(field_name)
            if value is not None and value != "":
                return value
        return None

    @staticmethod
    def _count_by_field(
        records: Iterable[Mapping[str, Any]],
        *,
        field_candidates: Sequence[str],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in records:
            value = ReportDataService._first_present(record, field_candidates)
            key = "unassigned" if value is None else str(value)
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: item[0].lower()))

    @staticmethod
    def _safe_integer(value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _sortable_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return datetime.min.replace(tzinfo=timezone.utc)
        else:
            return datetime.min.replace(tzinfo=timezone.utc)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _is_task_overdue(task: Mapping[str, Any]) -> bool:
        status = str(
            ReportDataService._first_present(task, ("status", "task_status"))
            or ""
        ).lower()
        if status in {
            "completed",
            "closed",
            "cancelled",
            "canceled",
            "done",
        }:
            return False

        due_value = ReportDataService._first_present(
            task,
            ("due_at", "due_date", "deadline", "target_completion_at"),
        )
        if due_value is None:
            return False
        return (
            ReportDataService._sortable_datetime(due_value)
            < datetime.now(timezone.utc)
        )
