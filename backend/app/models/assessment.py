"""Assessment models: config, records, questions, reports."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.db.database import Base


class ChapterAssessmentConfig(Base):
    """Teacher's preset configuration for chapter assessment."""
    __tablename__ = "chapter_assessment_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), unique=True, nullable=False)
    knowledge_points = Column(Text, nullable=False)  # JSON array
    question_types = Column(Text, nullable=False)     # JSON: {"choice": 2, "true_false": 2, "short_answer": 2}
    evaluation_dimensions = Column(Text, nullable=False)  # JSON: [{"name": "...", "weight": 0.4}, ...]
    total_questions = Column(Integer, default=0)
    time_limit_minutes = Column(Integer, nullable=True)
    passing_score = Column(Integer, default=60)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AssessmentRecord(Base):
    """A student's assessment attempt."""
    __tablename__ = "assessment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    config_id = Column(Integer, ForeignKey("chapter_assessment_configs.id"), nullable=True)
    status = Column(String(20), default="in_progress")  # in_progress | completed
    total_questions = Column(Integer, nullable=False)
    answered_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_score = Column(Numeric(5, 2), nullable=True)  # percentage 0-100
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AssessmentQuestion(Base):
    """Individual question within an assessment."""
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("assessment_records.id"), nullable=False)
    question_index = Column(Integer, nullable=False)
    question_type = Column(String(20), nullable=False)  # choice | true_false | short_answer
    question_content = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON array for choices
    correct_answer = Column(Text, nullable=True)
    user_answer = Column(Text, nullable=True)
    score = Column(Numeric(5, 2), default=0)
    is_correct = Column(Boolean, nullable=True)
    ai_evaluation = Column(Text, nullable=True)  # LLM feedback for short answers
    explanation = Column(Text, nullable=True)  # LLM correction/explanation for wrong answers
    created_at = Column(DateTime, server_default=func.now())


class AssessmentReport(Base):
    """Generated evaluation report for a completed assessment."""
    __tablename__ = "assessment_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("assessment_records.id"), unique=True, nullable=False)
    overall_score = Column(Numeric(5, 2), nullable=False)
    dimension_scores = Column(Text, nullable=False)  # JSON array
    summary_comment = Column(Text, nullable=True)
    review_suggestions = Column(Text, nullable=True)  # JSON array
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())
