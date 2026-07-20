from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from backend.app.core.dependencies import CommentReader, CommentWriter
from backend.app.db.session import get_db
from backend.app.schemas.case_comment import (
    CaseCommentCreate,
    CaseCommentListResponse,
    CaseCommentResponse,
    CaseCommentRevisionResponse,
    CaseCommentUpdate,
)
from backend.app.services.case_comment_service import (
    CaseCommentNotFoundError,
    CaseCommentPermissionError,
    DeletedCaseCommentError,
    create_case_comment,
    delete_case_comment,
    get_case_comment,
    list_case_comments,
    list_comment_revisions,
    serialize_comment,
    update_case_comment,
)


router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Case Comments"],
)


def _raise_comment_error(error: ValueError) -> None:
    if isinstance(error, CaseCommentNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error

    if isinstance(error, CaseCommentPermissionError):
        raise HTTPException(status_code=403, detail=str(error)) from error

    raise HTTPException(status_code=400, detail=str(error)) from error


@router.post(
    "/{case_id}/comments",
    response_model=CaseCommentResponse,
)
def create_comment(
    case_id: int,
    payload: CaseCommentCreate,
    request: Request,
    current_user: CommentWriter,
    db: Session = Depends(get_db),
):
    try:
        comment = create_case_comment(
            db,
            case_id=case_id,
            content=payload.content,
            visibility=payload.visibility,
            actor=current_user,
            request=request,
        )
        return serialize_comment(comment)
    except ValueError as error:
        _raise_comment_error(error)


@router.get(
    "/{case_id}/comments",
    response_model=CaseCommentListResponse,
)
def list_comments(
    case_id: int,
    current_user: CommentReader,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        comments, total = list_case_comments(
            db,
            case_id=case_id,
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
        return {
            "items": [serialize_comment(comment) for comment in comments],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except ValueError as error:
        _raise_comment_error(error)


@router.get(
    "/{case_id}/comments/{comment_id}/revisions",
    response_model=list[CaseCommentRevisionResponse],
)
def read_comment_revisions(
    case_id: int,
    comment_id: int,
    request: Request,
    current_user: CommentReader,
    db: Session = Depends(get_db),
):
    try:
        get_case_comment(
            db,
            case_id=case_id,
            comment_id=comment_id,
            current_user=current_user,
            request=request,
        )
        return list_comment_revisions(db, comment_id=comment_id)
    except ValueError as error:
        _raise_comment_error(error)


@router.get(
    "/{case_id}/comments/{comment_id}",
    response_model=CaseCommentResponse,
)
def read_comment(
    case_id: int,
    comment_id: int,
    request: Request,
    current_user: CommentReader,
    db: Session = Depends(get_db),
):
    try:
        comment = get_case_comment(
            db,
            case_id=case_id,
            comment_id=comment_id,
            current_user=current_user,
            request=request,
        )
        return serialize_comment(comment)
    except ValueError as error:
        _raise_comment_error(error)


@router.patch(
    "/{case_id}/comments/{comment_id}",
    response_model=CaseCommentResponse,
)
def edit_comment(
    case_id: int,
    comment_id: int,
    payload: CaseCommentUpdate,
    request: Request,
    current_user: CommentWriter,
    db: Session = Depends(get_db),
):
    try:
        get_case_comment(
            db,
            case_id=case_id,
            comment_id=comment_id,
            current_user=current_user,
            request=request,
        )
        comment = update_case_comment(
            db,
            comment_id=comment_id,
            payload=payload,
            actor=current_user,
            request=request,
        )
        return serialize_comment(comment)
    except (
        CaseCommentNotFoundError,
        CaseCommentPermissionError,
        DeletedCaseCommentError,
    ) as error:
        _raise_comment_error(error)


@router.delete(
    "/{case_id}/comments/{comment_id}",
    response_model=CaseCommentResponse,
)
def remove_comment(
    case_id: int,
    comment_id: int,
    request: Request,
    current_user: CommentWriter,
    db: Session = Depends(get_db),
):
    try:
        get_case_comment(
            db,
            case_id=case_id,
            comment_id=comment_id,
            current_user=current_user,
            request=request,
        )
        comment = delete_case_comment(
            db,
            comment_id=comment_id,
            actor=current_user,
            request=request,
        )
        return serialize_comment(comment)
    except (CaseCommentNotFoundError, CaseCommentPermissionError) as error:
        _raise_comment_error(error)
