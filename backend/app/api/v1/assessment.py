"""Assessment API routes."""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, require_teacher, require_student
from app.core.config import settings
from app.models.user import User
from app.models.chapter import Chapter
from app.models.assessment import (
    ChapterAssessmentConfig,
    AssessmentRecord,
    AssessmentQuestion,
    AssessmentReport,
)
from app.models.progress import ChapterProgress
from app.schemas.assessment import (
    AssessmentConfigCreate,
    AssessmentConfigResponse,
    AnswerSubmit,
    QuestionResponse,
    AssessmentRecordResponse,
    ReportResponse,
    QuestionReviewItem,
)
from app.services.assessment.question_generator import generate_questions
from app.services.assessment.answer_evaluator import evaluate_answers
from app.services.assessment.report_generator import generate_report
from app.utils.logger import log_info

router = APIRouter()


# ── Assessment Config (Teacher) ──

@router.get("/configs/chapter/{chapter_id}", response_model=AssessmentConfigResponse)
def get_config(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get assessment configuration for a chapter."""
    config = db.query(ChapterAssessmentConfig).filter(
        ChapterAssessmentConfig.chapter_id == chapter_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="该章节尚未配置考核")
    return AssessmentConfigResponse.model_validate(config)


@router.post("/configs", response_model=AssessmentConfigResponse)
def create_or_update_config(
    data: AssessmentConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """Create or update assessment config for a chapter (teacher only)."""
    # Check chapter exists
    chapter = db.query(Chapter).filter(Chapter.id == data.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    existing = db.query(ChapterAssessmentConfig).filter(
        ChapterAssessmentConfig.chapter_id == data.chapter_id
    ).first()

    def _serialize_for_db(data_dict: dict) -> dict:
        """JSON-encode list/dict values for Text columns."""
        result = {}
        for k, v in data_dict.items():
            if isinstance(v, (list, dict)):
                result[k] = json.dumps(v, ensure_ascii=False)
            else:
                result[k] = v
        return result

    if existing:
        update_data = _serialize_for_db(data.model_dump(exclude_unset=True))
        for key, value in update_data.items():
            setattr(existing, key, value)
        config = existing
    else:
        config = ChapterAssessmentConfig(**_serialize_for_db(data.model_dump()))
        db.add(config)

    # Calculate total questions
    total = 0
    if isinstance(data.question_types, dict):
        total = sum(data.question_types.values())
    elif isinstance(data.question_types, str):
        try:
            total = sum(json.loads(data.question_types).values())
        except (json.JSONDecodeError, TypeError):
            pass
    config.total_questions = total
    config.created_by = current_user.id
    db.commit()
    db.refresh(config)
    log_info("assessment", f"配置章节考核: {chapter.title}", user_id=current_user.id)
    return AssessmentConfigResponse.model_validate(config)


# ── Assessment Taking (Student) ──

@router.post("/start/{chapter_id}", response_model=dict)
def start_assessment(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new assessment for a chapter."""
    # Check config exists
    config = db.query(ChapterAssessmentConfig).filter(
        ChapterAssessmentConfig.chapter_id == chapter_id
    ).first()
    if not config:
        raise HTTPException(status_code=400, detail="该章节尚未配置考核题目")

    # Generate questions via LLM
    questions_data = generate_questions(config, chapter_id, db)

    # Create assessment record
    record = AssessmentRecord(
        user_id=current_user.id,
        chapter_id=chapter_id,
        config_id=config.id,
        status="in_progress",
        total_questions=len(questions_data),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Save questions
    for i, q in enumerate(questions_data):
        question = AssessmentQuestion(
            record_id=record.id,
            question_index=i,
            question_type=q["type"],
            question_content=q["question"],
            options=json.dumps(q.get("options", []), ensure_ascii=False) if q.get("options") else None,
            correct_answer=q.get("correct_answer"),
        )
        db.add(question)
    db.commit()

    # Update chapter progress
    progress = db.query(ChapterProgress).filter(
        ChapterProgress.user_id == current_user.id,
        ChapterProgress.chapter_id == chapter_id,
    ).first()
    if not progress:
        progress = ChapterProgress(
            user_id=current_user.id,
            chapter_id=chapter_id,
            status="pending",
        )
        db.add(progress)
    else:
        progress.status = "pending"
    db.commit()

    log_info("assessment", f"开始考核: 章节{chapter_id}", user_id=current_user.id)
    return {"record_id": record.id, "total_questions": len(questions_data)}


@router.get("/{record_id}/question")
def get_current_question(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current unanswered question."""
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == record_id).first()
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="考核记录不存在")

    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.record_id == record_id)
        .order_by(AssessmentQuestion.question_index.asc())
        .all()
    )

    for q in questions:
        if q.user_answer is None:
            return QuestionResponse.model_validate(q)

    # All answered
    return {"message": "所有题目已作答", "status": "complete"}


@router.post("/{record_id}/answer")
def submit_answer(
    record_id: int,
    data: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit answer for a question."""
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == record_id).first()
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="考核记录不存在")

    question = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.id == data.question_id,
        AssessmentQuestion.record_id == record_id,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    question.user_answer = data.answer
    record.answered_questions += 1
    db.commit()

    # Check if all answered
    total = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.record_id == record_id,
        AssessmentQuestion.user_answer.is_(None),
    ).count()

    if total == 0:
        return {
            "status": "completed",
            "message": "所有题目已作答，请提交",
            "answered": record.answered_questions,
            "total": record.total_questions,
        }

    # Return next question
    next_q = (
        db.query(AssessmentQuestion)
        .filter(
            AssessmentQuestion.record_id == record_id,
            AssessmentQuestion.user_answer.is_(None),
        )
        .order_by(AssessmentQuestion.question_index.asc())
        .first()
    )
    return {
        "status": "continue",
        "next_question": QuestionResponse.model_validate(next_q),
        "answered": record.answered_questions,
        "total": record.total_questions,
    }


@router.post("/{record_id}/submit", response_model=dict)
def submit_assessment(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit all answers, evaluate, and generate report."""
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == record_id).first()
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="考核记录不存在")

    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.record_id == record_id)
        .order_by(AssessmentQuestion.question_index.asc())
        .all()
    )

    # Evaluate answers
    evaluate_answers(questions, db)

    # Calculate score
    total_score = sum(float(q.score) for q in questions) / len(questions) if questions else 0
    correct_count = sum(1 for q in questions if q.is_correct)

    record.total_score = total_score
    record.correct_answers = correct_count
    record.status = "completed"
    record.completed_at = datetime.utcnow()
    db.commit()

    # Generate report
    report = generate_report(record, questions, db)

    # Update chapter progress
    progress = db.query(ChapterProgress).filter(
        ChapterProgress.user_id == current_user.id,
        ChapterProgress.chapter_id == record.chapter_id,
    ).first()
    if progress:
        progress.status = "completed"
        progress.best_score = total_score
        progress.assessment_count += 1
        progress.completed_at = datetime.utcnow()
        db.commit()

    log_info("assessment", f"完成考核: 章节{record.chapter_id}, 得分{total_score:.1f}", user_id=current_user.id)
    return {
        "record_id": record_id,
        "total_score": total_score,
        "correct_answers": correct_count,
        "total_questions": record.total_questions,
        "report_id": report.id if report else None,
    }


@router.get("/{record_id}/report", response_model=ReportResponse)
def get_report(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get assessment report."""
    report = db.query(AssessmentReport).filter(
        AssessmentReport.record_id == record_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="评价报告不存在")
    return ReportResponse.model_validate(report)


@router.get("/history", response_model=list)
def get_assessment_history(
    chapter_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get student's assessment history."""
    query = db.query(AssessmentRecord).filter(
        AssessmentRecord.user_id == current_user.id
    )
    if chapter_id:
        query = query.filter(AssessmentRecord.chapter_id == chapter_id)
    records = query.order_by(AssessmentRecord.created_at.desc()).all()
    return [AssessmentRecordResponse.model_validate(r) for r in records]


@router.get("/{record_id}/review", response_model=list[QuestionReviewItem])
def get_assessment_review(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the full per-question review for a completed assessment:
    question content, user answer, correct answer, score, AI evaluation,
    and a detailed correction/explanation (especially useful for wrong
    answers).
    """
    record = db.query(AssessmentRecord).filter(AssessmentRecord.id == record_id).first()
    if not record or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="考核记录不存在")

    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.record_id == record_id)
        .order_by(AssessmentQuestion.question_index.asc())
        .all()
    )

    results = []
    for q in questions:
        options_list = None
        if q.options:
            try:
                options_list = json.loads(q.options)
            except (json.JSONDecodeError, TypeError):
                options_list = None
        results.append(
            QuestionReviewItem(
                id=q.id,
                question_index=q.question_index,
                question_type=q.question_type,
                question_content=q.question_content,
                options=options_list,
                user_answer=q.user_answer,
                correct_answer=q.correct_answer,
                is_correct=q.is_correct,
                score=float(q.score) if q.score is not None else None,
                ai_evaluation=q.ai_evaluation,
                explanation=q.explanation,
            )
        )
    return results
