"""Question generator using LLM.

Generates assessment questions based on chapter content and
teacher-configured question types and knowledge points.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.assessment import ChapterAssessmentConfig
from app.services.llm.dashscope_client import chat

logger = logging.getLogger("course_agent.assessment.question_generator")

_MAX_RETRIES = 3


def _build_generation_prompt(
    config: ChapterAssessmentConfig,
    chapter: Chapter,
) -> List[Dict[str, str]]:
    """Build the LLM prompt for question generation."""
    knowledge_points = config.knowledge_points
    if isinstance(knowledge_points, str):
        try:
            knowledge_points = json.loads(knowledge_points)
        except (json.JSONDecodeError, TypeError):
            knowledge_points = []

    question_types = config.question_types
    if isinstance(question_types, str):
        try:
            question_types = json.loads(question_types)
        except (json.JSONDecodeError, TypeError):
            question_types = {}

    types_description = []
    for qt, count in question_types.items():
        type_name = {
            "choice": "选择题(choice)",
            "true_false": "判断题(true_false)",
            "short_answer": "简答题(short_answer)",
        }.get(qt, qt)
        types_description.append(f"  - {type_name}: {count}道")

    sys_prompt = """你是一位专业的课程考核出题专家。请根据提供的章节信息和知识点，生成考核题目。

要求：
1. 题目必须紧扣章节内容和知识点
2. 题目难度适中，既考察基础知识也考察理解应用
3. 选择题必须有4个选项（A、B、C、D），且只有一个正确答案
4. 判断题答案为"正确"或"错误"
5. 简答题需要提供参考答案要点
6. 严格按照指定的题目类型和数量生成

请以JSON格式返回，格式为：
{
  "questions": [
    {
      "type": "choice",
      "question": "题目内容",
      "options": ["A选项", "B选项", "C选项", "D选项"],
      "correct_answer": "A"
    },
    {
      "type": "true_false",
      "question": "题目内容",
      "correct_answer": "正确"
    },
    {
      "type": "short_answer",
      "question": "题目内容",
      "correct_answer": "参考答案要点"
    }
  ]
}

只返回JSON，不要包含其他文字说明。"""

    user_content = f"""章节标题: {chapter.title}
章节描述: {chapter.description or '无'}

知识点: {json.dumps(knowledge_points, ensure_ascii=False)}

需要生成的题目类型和数量:
{chr(10).join(types_description)}

请严格按照以上要求生成题目。"""

    return [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content},
    ]


def _validate_question(q: Dict[str, Any]) -> bool:
    """Validate a single question dict has the required fields."""
    if "type" not in q or "question" not in q or "correct_answer" not in q:
        return False
    if q["type"] == "choice":
        if "options" not in q or not isinstance(q["options"], list) or len(q["options"]) < 2:
            return False
    if q["type"] not in ("choice", "true_false", "short_answer"):
        return False
    return True


def generate_questions(
    config: ChapterAssessmentConfig,
    chapter_id: int,
    db: Session,
) -> List[Dict[str, Any]]:
    """Generate assessment questions using LLM.

    Args:
        config: The chapter assessment configuration.
        chapter_id: The chapter ID to generate questions for.
        db: Database session for querying chapter info.

    Returns:
        A list of question dicts, each containing:
            - type: "choice", "true_false", or "short_answer"
            - question: The question text
            - options: List of options (for choice type)
            - correct_answer: The correct answer
    """
    # Get chapter info
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        logger.error(f"Chapter {chapter_id} not found")
        return []

    messages = _build_generation_prompt(config, chapter)

    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            response_text = chat(messages)
            if not response_text:
                last_error = "Empty response from LLM"
                logger.warning(f"Question gen attempt {attempt + 1}: {last_error}")
                continue

            # Clean response — remove markdown fences if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)

            questions = data.get("questions", data if isinstance(data, list) else [])
            if isinstance(questions, dict):
                questions = questions.get("questions", [])

            if not isinstance(questions, list):
                last_error = "Response did not contain a questions list"
                continue

            # Validate and filter
            valid_questions = [q for q in questions if _validate_question(q)]
            if not valid_questions:
                last_error = "No valid questions found in response"
                continue

            logger.info(
                f"Generated {len(valid_questions)} questions "
                f"for chapter {chapter_id} (attempt {attempt + 1})"
            )
            return valid_questions

        except json.JSONDecodeError as e:
            last_error = f"JSON parse error: {e}"
            logger.warning(f"Question gen attempt {attempt + 1}: {last_error}")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Question gen attempt {attempt + 1}: {last_error}")

    logger.error(
        f"Failed to generate questions for chapter {chapter_id} "
        f"after {_MAX_RETRIES} attempts: {last_error}"
    )
    return []
