"""Chapter Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChapterCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order_index: Optional[int] = None


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class ChapterResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    order_index: int
    is_active: bool
    document_count: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChapterReorder(BaseModel):
    chapter_ids: List[int]
