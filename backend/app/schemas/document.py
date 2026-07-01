"""Document Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentCreate(BaseModel):
    chapter_id: Optional[int] = None
    title: str
    file_type: str
    file_path: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None


class DocumentResponse(BaseModel):
    id: int
    chapter_id: Optional[int] = None
    title: str
    file_type: str
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
