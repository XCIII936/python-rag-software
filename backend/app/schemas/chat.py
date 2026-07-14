"""Chat Pydantic schemas."""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Any
from pydantic import BaseModel, Field, model_validator


BEIJING_TZ = timezone(timedelta(hours=8))


def _to_beijing(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert a naive (UTC) datetime to Beijing time."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BEIJING_TZ)


class SessionCreate(BaseModel):
    title: Optional[str] = None
    chapter_id: Optional[int] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None


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

    @model_validator(mode="after")
    def _convert_timezone(self) -> "SessionResponse":
        self.created_at = _to_beijing(self.created_at)
        self.updated_at = _to_beijing(self.updated_at)
        return self


class MessageSend(BaseModel):
    content: str = Field(..., min_length=1)
    chapter_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    meta_info: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def _convert_timezone(self) -> "MessageResponse":
        self.created_at = _to_beijing(self.created_at)
        return self
