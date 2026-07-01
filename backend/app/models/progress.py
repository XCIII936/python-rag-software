"""Chapter progress model for tracking student learning path."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.sql import func
from app.db.database import Base


class ChapterProgress(Base):
    __tablename__ = "chapter_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    status = Column(String(20), default="to_learn")  # to_learn | pending | completed
    best_score = Column(Numeric(5, 2), nullable=True)
    assessment_count = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "chapter_id", name="uq_user_chapter"),
    )
