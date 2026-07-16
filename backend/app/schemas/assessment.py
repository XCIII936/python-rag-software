"""Assessment Pydantic schemas."""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class AssessmentConfigCreate(BaseModel):
    chapter_id: int
    knowledge_points: Any  # JSON: list of strings
    question_types: Any    # JSON: {"choice": 2, "true_false": 2, "short_answer": 2}
    evaluation_dimensions: Any  # JSON: [{"name": "...", "weight": 0.4}]
    total_questions: Optional[int] = None
    passing_score: Optional[int] = 60


class AssessmentConfigResponse(BaseModel):
    id: int
    chapter_id: int
    knowledge_points: Any
    question_types: Any
    evaluation_dimensions: Any
    total_questions: Optional[int] = None
    passing_score: Optional[int] = 60

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    question_id: int
    answer: str


class QuestionResponse(BaseModel):
    id: int
    question_index: int
    question_type: str
    question_content: str
    options: Optional[str] = None  # JSON string

    class Config:
        from_attributes = True


class AssessmentRecordResponse(BaseModel):
    id: int
    chapter_id: int
    status: str
    total_questions: int
    answered_questions: int
    total_score: Optional[float] = None
    started_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: int
    record_id: int
    overall_score: float
    dimension_scores: Any
    summary_comment: Optional[str] = None
    review_suggestions: Optional[Any] = None
    strengths: Optional[Any] = None
    weaknesses: Optional[Any] = None

    class Config:
        from_attributes = True


class QuestionReviewItem(BaseModel):
    """Full per-question review: content, answers, score, and AI correction."""

    id: int
    question_index: int
    question_type: str
    question_content: str
    options: Optional[List[str]] = None
    user_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    ai_evaluation: Optional[str] = None
    explanation: Optional[str] = None

    class Config:
        from_attributes = True
