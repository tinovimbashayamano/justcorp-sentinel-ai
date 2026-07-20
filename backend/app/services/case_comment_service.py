from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from backend.app.core.audit import AuditAction, AuditStatus
from backend.app.core.case_comments import CommentVisibility
from backend.app.core.case_history import CaseEvent
from backend.app.models.case_comment import CaseComment
from backend.app.models.case_comment_revision import CaseCommentRevision
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.user import User, UserRole
from backend.app.schemas.case_comment import CaseCommentUpdate
from backend.app.services.audit_service import create_audit_log
from backend.app.services.case_history_service import create_case_history


DELETED_COMMENT_MARKER = "[comment deleted]"


class CaseCommentNotFoundError(ValueError):
    pass


class CaseCommentPermissionError(ValueError):
    pass


class DeletedCaseCommentError(ValueError):
    pass


def _get_case(db: Session, case_id: int) -> FraudCaseReview:
    fraud_case = db.get(FraudCaseReview, case_id)

    if fraud_case is None:
        raise CaseCommentNotFoundError(f"Fraud case {case_id} not found.")

    return fraud_case


def _get_comment_for_case(
    db: Session,
    *,
    case_id: int,
    comment_id: int,
) -> CaseComment:
    _get_case(db, case_id)
    comment = (
        db.query(CaseComment)
        .filter(
            CaseComment.id == comment_id,
            CaseComment.case_id == case_id,
        )
        .first()
    )

    if comment is None:
        raise CaseCommentNotFoundError("Case comment not found.")

    return comment


def _audit_access_denied(
    db: Session,
    *,
    actor: User,
    operation: str,
    comment: CaseComment,
    request: Request | None,
) -> None:
    create_audit_log(
        db=db,
        action=AuditAction.CASE_COMMENT_ACCESS_DENIED,
        status=AuditStatus.DENIED,
        user=actor,
        resource_type="case_comment",
        resource_id=comment.id,
        request=request,
        details={
            "case_id": comment.case_id,
            "operation": operation,
        },
    )


def serialize_comment(comment: CaseComment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "case_id": comment.case_id,
        "author_user_id": comment.author_user_id,
        "author_username": comment.author_username,
        "content": (
            DELETED_COMMENT_MARKER if comment.is_deleted else comment.content
        ),
        "visibility": comment.visibility,
        "is_edited": comment.is_edited,
        "is_deleted": comment.is_deleted,
        "deleted_by_username": comment.deleted_by_username,
        "deleted_at": comment.deleted_at,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


def create_case_comment(
    db: Session,
    *,
    case_id: int,
    content: str,
    visibility: CommentVisibility,
    actor: User,
    request: Request | None = None,
) -> CaseComment:
    fraud_case = _get_case(db, case_id)
    validated_visibility = CommentVisibility(visibility)
    comment = CaseComment(
        case_id=case_id,
        author_user_id=actor.id,
        author_username=actor.username,
        content=content,
        visibility=validated_visibility.value,
    )

    try:
        db.add(comment)
        db.flush()
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=CaseEvent.COMMENT_CREATED,
            details={
                "comment_id": comment.id,
                "author_username": actor.username,
                "visibility": validated_visibility.value,
            },
            commit=False,
        )
        create_audit_log(
            db=db,
            action=AuditAction.CASE_COMMENT_CREATE,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type="case_comment",
            resource_id=comment.id,
            request=request,
            details={
                "case_id": case_id,
                "visibility": validated_visibility.value,
            },
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(comment)
    return comment


def get_case_comment(
    db: Session,
    *,
    case_id: int,
    comment_id: int,
    current_user: User,
    request: Request | None = None,
) -> CaseComment:
    comment = _get_comment_for_case(
        db,
        case_id=case_id,
        comment_id=comment_id,
    )

    if (
        current_user.role == UserRole.AUDITOR
        and comment.visibility != CommentVisibility.AUDITOR_VISIBLE
    ):
        _audit_access_denied(
            db,
            actor=current_user,
            operation="read",
            comment=comment,
            request=request,
        )
        raise CaseCommentNotFoundError("Case comment not found.")

    if current_user.role == UserRole.VIEWER:
        _audit_access_denied(
            db,
            actor=current_user,
            operation="read",
            comment=comment,
            request=request,
        )
        raise CaseCommentPermissionError(
            "You do not have permission to read this comment."
        )

    return comment


def list_case_comments(
    db: Session,
    *,
    case_id: int,
    current_user: User,
    include_deleted: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[CaseComment], int]:
    _get_case(db, case_id)

    if current_user.role == UserRole.VIEWER:
        raise CaseCommentPermissionError(
            "You do not have permission to read case comments."
        )

    query = db.query(CaseComment).filter(CaseComment.case_id == case_id)

    if current_user.role == UserRole.AUDITOR:
        query = query.filter(
            CaseComment.visibility == CommentVisibility.AUDITOR_VISIBLE
        )

    total = query.count()
    comments = (
        query.order_by(CaseComment.created_at.asc(), CaseComment.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return comments, total


def update_case_comment(
    db: Session,
    *,
    comment_id: int,
    payload: CaseCommentUpdate,
    actor: User,
    request: Request | None = None,
) -> CaseComment:
    comment = db.get(CaseComment, comment_id)

    if comment is None:
        raise CaseCommentNotFoundError("Case comment not found.")

    if actor.role != UserRole.ADMIN and comment.author_user_id != actor.id:
        _audit_access_denied(
            db,
            actor=actor,
            operation="update",
            comment=comment,
            request=request,
        )
        raise CaseCommentPermissionError(
            "Only the author or an administrator may edit this comment."
        )

    if comment.is_deleted:
        raise DeletedCaseCommentError("Deleted comments cannot be edited.")

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    normalized_data = {
        field: value.value if isinstance(value, CommentVisibility) else value
        for field, value in update_data.items()
    }
    changed_fields = [
        field
        for field, value in normalized_data.items()
        if getattr(comment, field) != value
    ]

    if not changed_fields:
        return comment

    fraud_case = _get_case(db, comment.case_id)
    revision = CaseCommentRevision(
        comment_id=comment.id,
        editor_user_id=actor.id,
        editor_username=actor.username,
        previous_content=comment.content,
        previous_visibility=comment.visibility,
    )

    try:
        db.add(revision)

        for field in changed_fields:
            setattr(comment, field, normalized_data[field])

        comment.is_edited = True
        db.flush()
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=CaseEvent.COMMENT_UPDATED,
            details={
                "comment_id": comment.id,
                "editor_username": actor.username,
                "changed_fields": changed_fields,
            },
            commit=False,
        )
        create_audit_log(
            db=db,
            action=AuditAction.CASE_COMMENT_UPDATE,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type="case_comment",
            resource_id=comment.id,
            request=request,
            details={
                "case_id": comment.case_id,
                "changed_fields": changed_fields,
            },
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(comment)
    return comment


def delete_case_comment(
    db: Session,
    *,
    comment_id: int,
    actor: User,
    request: Request | None = None,
) -> CaseComment:
    comment = db.get(CaseComment, comment_id)

    if comment is None:
        raise CaseCommentNotFoundError("Case comment not found.")

    if actor.role != UserRole.ADMIN and comment.author_user_id != actor.id:
        _audit_access_denied(
            db,
            actor=actor,
            operation="delete",
            comment=comment,
            request=request,
        )
        raise CaseCommentPermissionError(
            "Only the author or an administrator may delete this comment."
        )

    if comment.is_deleted:
        return comment

    fraud_case = _get_case(db, comment.case_id)

    try:
        comment.is_deleted = True
        comment.deleted_at = datetime.now(timezone.utc)
        comment.deleted_by_user_id = actor.id
        comment.deleted_by_username = actor.username
        db.flush()
        create_case_history(
            db=db,
            case=fraud_case,
            user=actor,
            event_type=CaseEvent.COMMENT_DELETED,
            details={
                "comment_id": comment.id,
                "deleted_by_username": actor.username,
                "visibility": comment.visibility,
            },
            commit=False,
        )
        create_audit_log(
            db=db,
            action=AuditAction.CASE_COMMENT_DELETE,
            status=AuditStatus.SUCCESS,
            user=actor,
            resource_type="case_comment",
            resource_id=comment.id,
            request=request,
            details={
                "case_id": comment.case_id,
                "visibility": comment.visibility,
            },
            commit=False,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(comment)
    return comment


def list_comment_revisions(
    db: Session,
    *,
    comment_id: int,
) -> list[CaseCommentRevision]:
    return (
        db.query(CaseCommentRevision)
        .filter(CaseCommentRevision.comment_id == comment_id)
        .order_by(
            CaseCommentRevision.created_at.asc(),
            CaseCommentRevision.id.asc(),
        )
        .all()
    )
