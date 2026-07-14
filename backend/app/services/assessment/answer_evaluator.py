"""Answer evaluator.

Evaluates student answers against correct answers.
- Choice / True-False: direct string comparison.
- Short answer: LLM-based evaluation with a score 0-100.
"""

import json
import logging
from typing import List

from sqlalchemy.orm import Session

from app.models.assessment import AssessmentQuestion
from app.models.llm_config import LlmConfig
from app.services.llm.dashscope_client import chat

logger = logging.getLogger("course_agent.assessment.evaluator")


def _normalize(text: str) -> str:
    """Strip and lower-case for comparison."""
    return text.strip().lower()


def _evaluate_short_answer(
    question_content: str,
    correct_answer: str,
    user_answer: str,
    llm_kwargs: dict,
) -> tuple:
    """Use LLM to evaluate a short answer.

    Returns:
        A tuple of (score: int 0-100, is_correct: bool, feedback: str).
    """
    prompt = [
        {
            "role": "system",
            "content": (
                "你是一位严谨的课程评分助手。你需要根据题目、参考答案和学生答案，"
                "评估学生答案的正确性和完整性。"
                "请给出0-100的分数，并给出简要评价。"
                "以JSON格式返回：{\"score\": 85, \"feedback\": \"评价内容\"}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"题目：{question_content}\n\n"
                f"参考答案：{correct_answer}\n\n"
                f"学生答案：{user_answer}\n\n"
                "请评分（0-100）并给出评价。"
            ),
        },
    ]

    try:
        response = chat(prompt, **llm_kwargs)
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        score = int(result.get("score", 0))
        score = max(0, min(100, score))
        feedback = result.get("feedback", "")

        is_correct = score >= 60
        return score, is_correct, feedback

    except Exception as exc:
        logger.error(f"Short answer evaluation failed: {exc}")
        return 0, False, f"评分失败: {str(exc)}"


def evaluate_answers(
    questions: List[AssessmentQuestion],
    db: Session,
) -> None:
    """Evaluate all questions in a record.

    For choice/true_false questions, compares the user answer to the correct
    answer directly. For short_answer questions, calls the LLM to score.

    Args:
        questions: List of AssessmentQuestion objects to evaluate.
        db: Database session (used for commits if needed by caller).

    Side effects:
        Updates the score, is_correct, and ai_evaluation fields of each
        AssessmentQuestion in-place. The caller is expected to commit.
    """
    # Query active LLM config for short-answer evaluation
    llm_config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
    llm_kwargs = {
        "provider": llm_config.provider if llm_config else "dashscope",
        "base_url": llm_config.base_url if llm_config else None,
        "model": llm_config.model_name if llm_config else None,
    }

    for question in questions:
        user_answer = (question.user_answer or "").strip()
        correct_answer = (question.correct_answer or "").strip()

        if not user_answer:
            question.score = 0
            question.is_correct = False
            question.ai_evaluation = "未作答"
            continue

        if question.question_type in ("choice", "true_false"):
            # Direct string comparison
            is_correct = _normalize(user_answer) == _normalize(correct_answer)
            question.score = 100.0 if is_correct else 0.0
            question.is_correct = is_correct
            question.ai_evaluation = (
                "正确" if is_correct else f"错误，正确答案是: {correct_answer}"
            )

        elif question.question_type == "short_answer":
            score, is_correct, feedback = _evaluate_short_answer(
                question_content=question.question_content,
                correct_answer=correct_answer,
                user_answer=user_answer,
                llm_kwargs=llm_kwargs,
            )
            question.score = float(score)
            question.is_correct = is_correct
            question.ai_evaluation = feedback

        else:
            logger.warning(f"Unknown question type: {question.question_type}")
            question.score = 0
            question.is_correct = False
            question.ai_evaluation = f"不支持的题型: {question.question_type}"

    db.commit()
    logger.info(
        f"Evaluated {len(questions)} questions, "
        f"correct: {sum(1 for q in questions if q.is_correct)}"
    )
