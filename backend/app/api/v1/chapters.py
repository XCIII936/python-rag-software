"""Chapter API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.user import User
from app.models.chapter import Chapter
from app.models.document import KnowledgeBaseDocument
from app.models.progress import ChapterProgress
from app.schemas.chapter import ChapterCreate, ChapterUpdate, ChapterResponse, ChapterReorder
from app.utils.logger import log_info

router = APIRouter()


def _chapter_response(chapter: Chapter, db: Session) -> ChapterResponse:
    """Build ChapterResponse with document count."""
    resp = ChapterResponse.model_validate(chapter)
    resp.document_count = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.chapter_id == chapter.id
    ).count()
    return resp


@router.get("", response_model=List[ChapterResponse])
def list_chapters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active chapters ordered by index."""
    chapters = (
        db.query(Chapter)
        .filter(Chapter.is_active == True)
        .order_by(Chapter.order_index.asc())
        .all()
    )
    return [_chapter_response(c, db) for c in chapters]


@router.post("", response_model=ChapterResponse)
def create_chapter(
    data: ChapterCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Create a new chapter (teacher only)."""
    # Auto-assign order index
    if data.order_index is None:
        max_order = db.query(Chapter).count()
        data.order_index = max_order
    chapter = Chapter(**data.model_dump())
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    log_info("chapter", f"创建章节: {chapter.title}")
    return ChapterResponse.model_validate(chapter)


@router.put("/reorder")
def reorder_chapters(
    data: ChapterReorder,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Reorder chapters (teacher only)."""
    for idx, cid in enumerate(data.chapter_ids):
        chapter = db.query(Chapter).filter(Chapter.id == cid).first()
        if chapter:
            chapter.order_index = idx
    db.commit()
    return {"message": "排序成功"}


@router.get("/progress")
def get_chapter_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get student's chapter progress."""
    chapters = (
        db.query(Chapter)
        .filter(Chapter.is_active == True)
        .order_by(Chapter.order_index.asc())
        .all()
    )
    progress_list = (
        db.query(ChapterProgress)
        .filter(ChapterProgress.user_id == current_user.id)
        .all()
    )
    progress_map = {p.chapter_id: p for p in progress_list}

    result = []
    for ch in chapters:
        prog = progress_map.get(ch.id)
        result.append({
            "chapter_id": ch.id,
            "title": ch.title,
            "order_index": ch.order_index,
            "status": prog.status if prog else "to_learn",
            "best_score": float(prog.best_score) if prog and prog.best_score else None,
        })
    return result


@router.get("/{chapter_id}", response_model=ChapterResponse)
def get_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single chapter by ID."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return _chapter_response(chapter, db)


@router.put("/{chapter_id}", response_model=ChapterResponse)
def update_chapter(
    chapter_id: int,
    data: ChapterUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Update a chapter (teacher only)."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(chapter, key, value)
    db.commit()
    db.refresh(chapter)
    return ChapterResponse.model_validate(chapter)


@router.delete("/{chapter_id}")
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Delete a chapter (teacher only)."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    chapter.is_active = False
    db.commit()
    log_info("chapter", f"删除章节: {chapter.title}")
    return {"message": "章节已删除"}
