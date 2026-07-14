"""Document upload and management API routes.

Includes background processing of uploaded documents:
1. Parse file content (PDF/PPT/Word parsers)
2. Split text into chunks (Chinese-aware)
3. Generate embeddings and index into Milvus
4. Update document status
"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.database import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.core.security import decode_token
from app.models.user import User
from app.models.chapter import Chapter
from app.models.document import KnowledgeBaseDocument
from app.schemas.document import DocumentResponse
from app.utils.file_utils import validate_file_upload, save_upload_file, delete_file, get_file_extension
from app.utils.logger import log_info

logger = logging.getLogger("course_agent.documents")

router = APIRouter()


# ── Background processing: parse → chunk → index to Milvus ──

def process_and_index_document(doc_id: int) -> None:
    """Parse, chunk, and index a document into Milvus (runs in background).

    This function opens its own DB session to avoid lifecycle issues.
    """
    from app.db.database import SessionLocal
    from app.services.rag.text_splitter import split_document
    from app.core.config import settings

    local_db = SessionLocal()
    try:
        doc = local_db.query(KnowledgeBaseDocument).filter(
            KnowledgeBaseDocument.id == doc_id
        ).first()
        if not doc:
            logger.warning(f"Document {doc_id} not found for processing")
            return

        # Mark as parsing
        doc.status = "parsing"
        local_db.commit()

        file_path = doc.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = get_file_extension(doc.title)
        source_name = doc.title
        all_text_segments = []

        # 1. Parse file based on extension
        if ext in (".pdf",):
            from app.services.document_parse.pdf_parser import parse_pdf
            parsed = parse_pdf(file_path)
            for p in parsed:
                text = p.get("content", "").strip()
                if text:
                    all_text_segments.append({
                        "content": text,
                        "metadata": {
                            "source": source_name,
                            "page": p.get("page_num", 1),
                            "file_type": "pdf",
                            "chapter_id": doc.chapter_id,
                            "document_id": doc.id,
                            "title": doc.title,
                        }
                    })
            doc.page_count = len(parsed)

        elif ext in (".ppt", ".pptx"):
            from app.services.document_parse.ppt_parser import parse_ppt
            parsed = parse_ppt(file_path)
            for p in parsed:
                text = p.get("content", "").strip()
                title_text = p.get("slide_title", "")
                full_text = f"{title_text}\n{text}" if title_text else text
                if full_text.strip():
                    all_text_segments.append({
                        "content": full_text,
                        "metadata": {
                            "source": source_name,
                            "page": p.get("slide_index", 1),
                            "file_type": "ppt",
                            "chapter_id": doc.chapter_id,
                            "document_id": doc.id,
                            "title": f"{source_name} - 第{p.get('slide_index', 1)}页",
                        }
                    })
            doc.page_count = len(parsed)

        elif ext in (".doc", ".docx"):
            from app.services.document_parse.word_parser import parse_word
            parsed = parse_word(file_path)
            # Group paragraphs into ~1500-char chunks
            buf = ""
            buf_start = 1
            seg_idx = 0
            for p in parsed:
                text = p.get("content", "").strip()
                if not text:
                    continue
                buf += text + "\n"
                if len(buf) >= 1500:
                    all_text_segments.append({
                        "content": buf.strip(),
                        "metadata": {
                            "source": source_name,
                            "page": seg_idx + 1,
                            "file_type": "doc",
                            "chapter_id": doc.chapter_id,
                            "document_id": doc.id,
                            "title": f"{source_name} - 段落{buf_start}-{p.get('paragraph_index', buf_start)}",
                        }
                    })
                    seg_idx += 1
                    buf = ""
                    buf_start = p.get("paragraph_index", buf_start) + 1
            if buf.strip():
                all_text_segments.append({
                    "content": buf.strip(),
                    "metadata": {
                        "source": source_name,
                        "page": seg_idx + 1,
                        "file_type": "doc",
                        "chapter_id": doc.chapter_id,
                        "document_id": doc.id,
                        "title": source_name,
                    }
                })
            doc.page_count = len(parsed)

        if not all_text_segments:
            logger.warning(f"No text content extracted from {doc.title}")
            doc.status = "parsed"
            doc.chunk_count = 0
            local_db.commit()
            return

        # 2. Split each segment into smaller chunks
        all_chunks = []
        for seg in all_text_segments:
            chunks = split_document(
                seg["content"],
                metadata=seg["metadata"],
                chunk_size=500,
                chunk_overlap=50,
            )
            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning(f"No chunks generated from {doc.title}")
            doc.status = "parsed"
            doc.chunk_count = 0
            local_db.commit()
            return

        # 3. Index into Milvus
        try:
            from langchain_milvus import Milvus as LangChainMilvus
            from app.services.rag.rag_chain import DashScopeEmbeddings

            embeddings = DashScopeEmbeddings()
            vectorstore = LangChainMilvus(
                embedding_function=embeddings,
                collection_name=settings.MILVUS_COLLECTION,
                connection_args={
                    "host": settings.MILVUS_HOST,
                    "port": settings.MILVUS_PORT,
                },
            )

            texts = [c["content"] for c in all_chunks]
            metadatas = [c["metadata"] for c in all_chunks]
            vectorstore.add_texts(texts=texts, metadatas=metadatas)
            doc.chunk_count = len(all_chunks)
            logger.info(f"Indexed {len(all_chunks)} chunks to Milvus for {doc.title}")

        except Exception as milvus_err:
            logger.warning(
                f"Milvus indexing skipped (Milvus may not be running): {milvus_err}"
            )
            doc.chunk_count = len(all_chunks)

        doc.status = "parsed"
        local_db.commit()
        logger.info(f"Document processing complete: {doc.title} ({doc.chunk_count} chunks)")

    except Exception as exc:
        logger.error(f"Document processing failed for doc {doc_id}: {exc}")
        try:
            doc_ref = local_db.query(KnowledgeBaseDocument).filter(
                KnowledgeBaseDocument.id == doc_id
            ).first()
            if doc_ref:
                doc_ref.status = "failed"
                doc_ref.error_message = str(exc)[:500]
                local_db.commit()
        except Exception:
            pass
    finally:
        local_db.close()


def _enrich_doc_response(doc: KnowledgeBaseDocument, db: Session) -> DocumentResponse:
    """Convert doc to response, resolving chapter title from DB."""
    resp = DocumentResponse.model_validate(doc)
    if doc.chapter_id:
        chapter = db.query(Chapter).filter(Chapter.id == doc.chapter_id).first()
        if chapter:
            resp.chapter_title = chapter.title
    return resp


# ── API Routes ──

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chapter_id: int = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """Upload a document file (teacher only). Auto-processes in background."""
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

    # Trigger background processing (parse → chunk → Milvus)
    if background_tasks:
        background_tasks.add_task(process_and_index_document, doc.id)

    log_info("upload", f"文档上传: {file.filename}", user_id=current_user.id)
    return _enrich_doc_response(doc, db)


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    chapter_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all knowledge base documents (authenticated users)."""
    query = db.query(KnowledgeBaseDocument).order_by(
        KnowledgeBaseDocument.created_at.desc()
    )
    if chapter_id:
        query = query.filter(KnowledgeBaseDocument.chapter_id == chapter_id)
    docs = query.all()
    return [_enrich_doc_response(d, db) for d in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Get a single document by ID."""
    doc = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.id == document_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return _enrich_doc_response(doc, db)


@router.get("/{document_id}/file")
def get_document_file(
    document_id: int,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    token: Optional[str] = Query(None, description="JWT token alternative (for browser-native navigation)"),
):
    """Serve document file for preview/download (authenticated users).

    Supports two auth methods:
    1. Authorization: Bearer <token> header (Axios/fetch)
    2. ?token=<token> query parameter (window.open / <a> download)
    """
    # Resolve token from header first, then query param
    token_str = None
    if credentials:
        token_str = credentials.credentials
    elif token:
        token_str = token

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token_str)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    doc = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.id == document_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在于服务器")
    return FileResponse(
        path=doc.file_path,
        filename=doc.title or os.path.basename(doc.file_path),
        media_type="application/octet-stream",
    )


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
    delete_file(doc.file_path)
    db.delete(doc)
    db.commit()
    log_info("upload", f"文档删除: {doc.title}")
    return {"message": "文档已删除"}


@router.post("/{document_id}/reprocess")
def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Re-process a document (teacher only)."""
    doc = db.query(KnowledgeBaseDocument).filter(
        KnowledgeBaseDocument.id == document_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc.status = "pending"
    doc.error_message = None
    db.commit()
    background_tasks.add_task(process_and_index_document, doc.id)
    return {"message": "文档已开始重新处理"}
