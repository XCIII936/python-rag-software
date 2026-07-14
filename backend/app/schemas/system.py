"""System management Pydantic schemas."""

from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel


class ActivityItem(BaseModel):
    id: int
    username: str
    action: str
    module: str
    detail: str
    created_at: Optional[datetime] = None


class LlmConfigUpdate(BaseModel):
    model_config = {'protected_namespaces': ()}
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    base_url: Optional[str] = None
    provider: Optional[str] = None


class LlmConfigResponse(BaseModel):
    model_config = {'protected_namespaces': (), 'from_attributes': True}
    id: int
    provider: str
    model_name: str
    base_url: str
    embedding_model: str
    temperature: float
    max_tokens: int
    top_p: float
    is_active: bool


class DashboardStats(BaseModel):
    total_students: int
    total_chapters: int
    total_documents: int
    total_assessments: int
    total_chat_sessions: int
    recent_activity: List[ActivityItem] = []


class LogQuery(BaseModel):
    level: Optional[str] = None
    module: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    skip: int = 0
    limit: int = 50


class LogResponse(BaseModel):
    id: int
    level: str
    module: str
    action: Optional[str] = None
    message: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
