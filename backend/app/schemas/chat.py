"""Chat Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: Optional[str] = None
    chapter_id: Optional[int] = None


class SessionResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    chapter_id: Optional[int] = None
    message_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageSend(BaseModel):
    content: str = Field(..., min_length=1)
    chapter_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    metadata: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
