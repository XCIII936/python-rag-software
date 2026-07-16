"""Answer evaluator.

Evaluates student answers against correct answers.
- Choice / True-False: direct string comparison, with an LLM-generated
  detailed explanation when the answer is wrong.
- Short answer: LLM-based evaluation with a score 0-100 plus a detailed
  correction explanation.
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
        A tuple of (score: int 0-100, is_correct: bool, feedback: str, explanation: str).
        `feedback` is a short overall comment; `explanation` is a detailed
        correction pointing out what was missing/wrong and the complete
        reference answer, to help the student learn from the mistake.
    """
    prompt = [
        {
            "role": "system",
            "content": (
                "你是一位严谨且善于讲解的课程评分助手。你需要根据题目、参考答案和学生答案，"
                "评估学生答案的正确性和完整性，并给出详细的纠正讲解。\n\n"
                "请给出0-100的分数，一句话简要评价（feedback），以及详细纠正说明（explanation）。\n"
                "explanation 要求：\n"
                "1. 指出学生答案中遗漏、错误或不准确的地方（若答案已完全正确，可说明其答对的关键点）；\n"
                "2. 给出完整、准确的参考答案讲解，帮助学生理解知识点；\n"
                "3. 语言简洁清晰，可分点表述。\n\n"
                "以JSON格式返回，不要包含其他文字：\n"
                "{\"score\": 85, \"feedback\": \"简要评价\", \"explanation\": \"详细纠正说明...\"}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"题目：{question_content}\n\n"
                f"参考答案：{correct_answer}\n\n"
                f"学生答案：{user_answer}\n\n"
                "请评分（0-100），给出简要评价和详细纠正说明。"
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
        explanation = result.get("explanation", "")

        is_correct = score >= 60
        return score, is_correct, feedback, explanation

    except Exception as exc:
        logger.error(f"Short answer evaluation failed: {exc}")
        return 0, False, f"评分失败: {str(exc)}", ""


def _generate_objective_explanation(
    question_content: str,
    options: str,
    correct_answer: str,
    user_answer: str,
    question_type: str,
    llm_kwargs: dict,
) -> str:
    """Generate a detailed correction/explanation for a wrong choice or
    true/false answer, explaining why the correct answer is right and
    (if relevant) why the student's chosen answer is a common misconception.

    Returns:
        The explanation text, or an empty string on failure.
    """
    options_text = f"\n选项：{options}" if options else ""
    prompt = [
        {
            "role": "system",
            "content": (
                "你是一位善于讲解的课程助教。学生在一道客观题（选择题/判断题）上答错了，"
                "请你给出简明的纠正讲解，说明正确答案的原因，并指出学生所选答案错在哪里"
                "（如果是常见误区，可以点明）。\n"
                "要求：2-4句话，直接讲解，不要输出JSON或多余格式。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"题目（{question_type}）：{question_content}{options_text}\n"
                f"正确答案：{correct_answer}\n"
                f"学生答案：{user_answer}\n\n"
                "请给出纠正讲解。"
            ),
        },
    ]
    try:
        response = chat(prompt, **llm_kwargs)
        return (response or "").strip()
    except Exception as exc:
        logger.warning(f"Objective explanation generation failed: {exc}")
        return ""


def evaluate_answers(
    questions: List[AssessmentQuestion],
    db: Session,
) -> None:
    """Evaluate all questions in a record.

    For choice/true_false questions, compares the user answer to the correct
    answer directly, and generates a detailed LLM explanation when wrong.
    For short_answer questions, calls the LLM to score and generate a
    detailed correction.

    Args:
        questions: List of AssessmentQuestion objects to evaluate.
        db: Database session (used for commits if needed by caller).

    Side effects:
        Updates the score, is_correct, ai_evaluation, and explanation
        fields of each AssessmentQuestion in-place. The caller is expected
        to commit (this function also commits at the end).
    """
    # Query active LLM config for LLM-based evaluation/explanation
    llm_config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
    llm_kwargs = {
        "provider": llm_config.provider if llm_config else "dashscope",
        "base_url": llm_config.base_url if llm_config else None,
        "model": llm_config.model_name if llm_config else None,
        "api_key": (llm_config.api_key if llm_config and llm_config.api_key else None),
    }

    for question in questions:
        user_answer = (question.user_answer or "").strip()
        correct_answer = (question.correct_answer or "").strip()

        if not user_answer:
            question.score = 0
            question.is_correct = False
            question.ai_evaluation = "未作答"
            question.explanation = (
                f"本题未作答。正确答案：{correct_answer}" if correct_answer else "本题未作答。"
            )
            continue

        if question.question_type in ("choice", "true_false"):
            # Direct string comparison
            is_correct = _normalize(user_answer) == _normalize(correct_answer)
            question.score = 100.0 if is_correct else 0.0
            question.is_correct = is_correct
            question.ai_evaluation = (
                "正确" if is_correct else f"错误，正确答案是: {correct_answer}"
            )

            if is_correct:
                question.explanation = ""
            else:
                question.explanation = _generate_objective_explanation(
                    question_content=question.question_content,
                    options=question.options or "",
                    correct_answer=correct_answer,
                    user_answer=user_answer,
                    question_type=question.question_type,
                    llm_kwargs=llm_kwargs,
                )

        elif question.question_type == "short_answer":
            score, is_correct, feedback, explanation = _evaluate_short_answer(
                question_content=question.question_content,
                correct_answer=correct_answer,
                user_answer=user_answer,
                llm_kwargs=llm_kwargs,
            )
            question.score = float(score)
            question.is_correct = is_correct
            question.ai_evaluation = feedback
            question.explanation = explanation

        else:
            logger.warning(f"Unknown question type: {question.question_type}")
            question.score = 0
            question.is_correct = False
            question.ai_evaluation = f"不支持的题型: {question.question_type}"
            question.explanation = ""

    db.commit()
    logger.info(
        f"Evaluated {len(questions)} questions, "
        f"correct: {sum(1 for q in questions if q.is_correct)}"
    )
