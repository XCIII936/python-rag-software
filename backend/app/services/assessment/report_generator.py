"""Report generator for assessment results.

Generates a comprehensive evaluation report including per-dimension
scores, summary comment, review suggestions, strengths, and weaknesses.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.llm_config import LlmConfig
from app.models.assessment import (
    AssessmentQuestion,
    AssessmentRecord,
    AssessmentReport,
    ChapterAssessmentConfig,
)
from app.services.llm.dashscope_client import chat

logger = logging.getLogger("course_agent.assessment.report")


def _calculate_dimension_scores(
    config: ChapterAssessmentConfig,
    questions: List[AssessmentQuestion],
) -> List[Dict[str, Any]]:
    """Calculate scores per evaluation dimension.

    Dimensions are defined in the config's evaluation_dimensions field.
    Each dimension has a name and weight. Questions are mapped to
    dimensions by their type.

    Args:
        config: Chapter assessment configuration with evaluation_dimensions.
        questions: The list of answered questions.

    Returns:
        A list of dicts with 'name', 'score', and 'weight' for each dimension.
    """
    dimensions = config.evaluation_dimensions
    if isinstance(dimensions, str):
        try:
            dimensions = json.loads(dimensions)
        except (json.JSONDecodeError, TypeError):
            dimensions = []

    if not dimensions:
        return []

    # Group questions by type
    type_scores: Dict[str, List[float]] = {}
    for q in questions:
        qt = q.question_type
        if qt not in type_scores:
            type_scores[qt] = []
        type_scores[qt].append(float(q.score) if q.score else 0.0)

    # Map dimensions to question types (simple heuristic)
    dimension_results = []
    for dim in dimensions:
        name = dim.get("name", "")
        weight = dim.get("weight", 0)

        # Try to match dimension name to question types
        matched_types = []
        for qt in type_scores:
            if name in ("基础知识", "基础", "knowledge"):
                if qt in ("choice", "true_false"):
                    matched_types.append(qt)
            elif name in ("理解应用", "理解", "comprehension"):
                if qt == "choice":
                    matched_types.append(qt)
            elif name in ("分析评价", "分析", "analysis"):
                if qt == "short_answer":
                    matched_types.append(qt)
            else:
                # Fallback: spread questions evenly
                matched_types.append(qt)

        if matched_types:
            all_scores = []
            for mt in set(matched_types):
                all_scores.extend(type_scores.get(mt, []))
            avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        else:
            avg_score = 0

        dimension_results.append({
            "name": name,
            "score": round(avg_score, 2),
            "weight": weight,
        })

    return dimension_results


def _build_report_prompt(
    record: AssessmentRecord,
    questions: List[AssessmentQuestion],
    dimension_scores: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Build the LLM prompt for generating the evaluation report."""
    # Build a summary of the assessment
    question_summaries = []
    for q in questions:
        question_summaries.append(
            f"  [{q.question_type}] {q.question_content[:100]}...\n"
            f"    得分: {float(q.score) if q.score else 0}/100\n"
            f"    评价: {q.ai_evaluation or ''}"
        )

    questions_text = "\n".join(question_summaries)
    dims_text = json.dumps(dimension_scores, ensure_ascii=False, indent=2)

    system_prompt = """你是一位专业的课程学习评估报告撰写专家。请根据学生的考核成绩，生成一份详细的评估报告。

要求：
1. 总结评语（summary_comment）：对学生整体表现的概括性评价，指出整体水平
2. 复习建议（review_suggestions）：具体的学习建议列表，帮助学生改进薄弱环节
3. 优势（strengths）：学生表现较好的方面列表
4. 不足（weaknesses）：学生需要加强的方面列表

请以JSON格式返回，不要包含其他文字：
{
  "summary_comment": "总结评语...",
  "review_suggestions": ["建议1", "建议2", ...],
  "strengths": ["优势1", "优势2", ...],
  "weaknesses": ["不足1", "不足2", ...]
}"""

    user_content = f"""考核总分: {float(record.total_score) if record.total_score else 0:.1f}/100
各维度得分: {dims_text}

题目详情:
{questions_text}

请根据以上信息生成评估报告。"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def generate_report(
    record: AssessmentRecord,
    questions: List[AssessmentQuestion],
    db: Session,
) -> Optional[AssessmentReport]:
    """Generate an evaluation report for a completed assessment.

    Args:
        record: The completed assessment record.
        questions: All questions in the record (with scores populated).
        db: Database session for queries and saves.

    Returns:
        The saved AssessmentReport object, or None on failure.
    """
    # Get config
    config = (
        db.query(ChapterAssessmentConfig)
        .filter(ChapterAssessmentConfig.id == record.config_id)
        .first()
    )

    # Calculate dimension scores
    if config:
        dimension_scores = _calculate_dimension_scores(config, questions)
    else:
        dimension_scores = []

    overall_score = float(record.total_score) if record.total_score else 0.0

    # Build LLM prompt and generate report content
    messages = _build_report_prompt(record, questions, dimension_scores)

    summary_comment = ""
    review_suggestions = []
    strengths = []
    weaknesses = []

    # Get active LLM config for provider selection
    llm_config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
    llm_kwargs = {
        "provider": llm_config.provider if llm_config else "dashscope",
        "base_url": llm_config.base_url if llm_config else None,
        "model": llm_config.model_name if llm_config else None,
    }

    try:
        response_text = chat(messages, **llm_kwargs)
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)

        summary_comment = result.get("summary_comment", "")
        review_suggestions = result.get("review_suggestions", [])
        strengths = result.get("strengths", [])
        weaknesses = result.get("weaknesses", [])

    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        summary_comment = "报告生成失败，请稍后重试。"

    # Save report
    report = AssessmentReport(
        record_id=record.id,
        overall_score=overall_score,
        dimension_scores=json.dumps(dimension_scores, ensure_ascii=False),
        summary_comment=summary_comment,
        review_suggestions=json.dumps(review_suggestions, ensure_ascii=False),
        strengths=json.dumps(strengths, ensure_ascii=False),
        weaknesses=json.dumps(weaknesses, ensure_ascii=False),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    logger.info(
        f"Report generated for record {record.id}, "
        f"overall score: {overall_score:.1f}"
    )
    return report
