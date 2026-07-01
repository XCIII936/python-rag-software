"""Agent configuration model."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.db.database import Base


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    model_name = Column(String(100), default="qwen3-max")
    temperature = Column(Numeric(3, 2), default=0.7)
    max_tokens = Column(Integer, default=2048)
    top_p = Column(Numeric(3, 2), default=0.9)
    parameters = Column(Text, nullable=True)  # JSON extra params
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
