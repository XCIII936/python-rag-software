"""Document upload and management API routes."""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.user import User
from app.models.document import KnowledgeBaseDocument
from app.schemas.document import DocumentResponse
from app.utils.file_utils import validate_file_upload, save_upload_file, delete_file, get_file_extension
from app.utils.logger import log_info

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chapter_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """Upload a document file (teacher only)."""
    validate_file_upload(file)
    file_path, file_name, file_size, file_hash = save_upload_file(file, "documents")

    doc = KnowledgeBaseDocument(
        chapter_id=chapter_id,
        title=file.filename,
        file_type=get_file_extension(file.filename).lstrip("."),
        file_path=file_path,
        file_size=file_size,
        file_hash=file_hash,
        status="pending",
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    log_info("upload", f"文档上传: {file.filename}", user_id=current_user.id)
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    chapter_id: int = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """List all knowledge base documents (teacher only)."""
    query = db.query(KnowledgeBaseDocument).order_by(
        KnowledgeBaseDocument.created_at.desc()
    )
    if chapter_id:
        query = query.filter(KnowledgeBaseDocument.chapter_id == chapter_id)
    docs = query.all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Delete a document and its file (teacher only)."""
    doc = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.id == document_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # Delete file from disk
    delete_file(doc.file_path)
    db.delete(doc)
    db.commit()
    log_info("upload", f"文档删除: {doc.title}")
    return {"message": "文档已删除"}


@router.post("/{document_id}/reprocess")
def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Mark a document for re-processing (teacher only)."""
    doc = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.id == document_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc.status = "pending"
    doc.error_message = None
    db.commit()
    return {"message": "文档已标记为重新处理"}
