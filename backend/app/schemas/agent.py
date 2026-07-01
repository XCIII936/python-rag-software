"""Agent Pydantic schemas."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_name: str = "qwen3-max"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    parameters: Optional[Any] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_name: str
    temperature: float
    max_tokens: int
    top_p: float
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
