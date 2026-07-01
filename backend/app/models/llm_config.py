"""LLM configuration model."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.sql import func
from app.db.database import Base


class LlmConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), default="dashscope")
    api_key = Column(String(500), nullable=True)
    api_key_encrypted = Column(Boolean, default=False)
    model_name = Column(String(100), default="qwen3-max")
    base_url = Column(String(500), default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    embedding_model = Column(String(100), default="text-embedding-v3")
    temperature = Column(Numeric(3, 2), default=0.7)
    max_tokens = Column(Integer, default=2048)
    top_p = Column(Numeric(3, 2), default=0.9)
    is_active = Column(Boolean, default=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
