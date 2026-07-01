"""Resource recommendation model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.db.database import Base


class ResourceRecommendation(Base):
    __tablename__ = "resource_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("knowledge_base_documents.id"), nullable=True)
    chunk_id = Column(String(100), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(50), nullable=False)  # ppt_slide | pdf_page | video_segment | chapter_section
    relevance_score = Column(Numeric(3, 2), nullable=True)
    source_info = Column(Text, nullable=True)  # JSON: {page_num, slide_index, timestamp}
    created_at = Column(DateTime, server_default=func.now())
