"""Chat API routes with SSE streaming — RAG-enhanced learning assistant."""

import json
import logging
from typing import List, Optional

logger = logging.getLogger("course_agent.chat")

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.llm_config import LlmConfig
from app.schemas.chat import SessionCreate, SessionUpdate, SessionResponse, MessageSend, MessageResponse
from app.services.llm.dashscope_client import stream_chat
from app.services.rag.rag_chain import query_knowledge_base
from app.services.recommendation.recommender import recommend_resources
from app.utils.logger import log_info

router = APIRouter()

# ── Learning Assistant System Prompt ──────────────────────────────────
LEARNING_ASSISTANT_PROMPT = """你是"课程教学助手"，一门**软件工程**课程的学习辅助 AI。你的职责是帮助学生深入理解课程知识、解答疑惑，并提供有针对性的学习指导。

## 核心行为准则

1. **基于课程资料回答** — 如果下方提供了「课程参考资料」，你必须优先使用其中的内容来回答问题。参考资料未覆盖时，可以基于你的知识补充，但需标注"这是我基于一般知识的补充"。
2. **引导式教学** — 不要直接告诉学生所有答案。多用提问引导学生自己思考（如"你觉得在这个场景下哪种模型更合适？"）。对简单问题可直接回答，对复杂问题分步引导。
3. **循序渐进** — 先判断学生的知识水平，从基础概念开始，逐步深入到高级话题。
4. **举例说明** — 每个抽象概念都尽可能配一个具体例子（代码片段、场景描述、类比等）。
5. **准确与诚实** — 如果不确定某个知识点，明确告知学生不确定，不要编造答案。
6. **鼓励与耐心** — 保持友好、鼓励的语气。肯定学生的提问，即使问题很简单。

## 课程范围

| 模块 | 核心内容 |
|------|---------|
| 软件工程概述 | 软件危机、软件过程模型（瀑布/敏捷/迭代） |
| 需求工程 | 需求获取、分析、规格说明、用例建模 |
| 软件设计与架构 | 设计原则（SOLID）、架构模式（MVC/微服务）、设计模式 |
| 软件实现 | 编码规范、代码重构、Git 版本控制、代码审查、单元测试 |
| 软件测试 | 白盒/黑盒测试、集成测试、系统测试、自动化测试 |
| 软件维护与项目管理 | 维护类型、配置管理、项目估算、风险管理 |
| 软件质量与过程改进 | 质量保证、CMMI、ISO 标准、持续改进 |
| 新兴方法 | DevOps、CI/CD、云原生、AI 辅助开发 |

## 回答格式建议

- **概念类问题**：简明定义 → 展开说明 → 实例
- **操作类问题**：分步骤说明，可含代码片段
- **对比类问题**：用表格对比异同
- **开放类问题**：给出多个视角，鼓励进一步探索
"""


def _build_system_message(
    db: Session,
    user_question: str,
    chapter_id: Optional[int] = None,
) -> tuple[str, bool]:
    """Build the system message: base prompt + optional RAG/chapter context.

    Returns:
        Tuple of (system_prompt, has_context) where has_context indicates
        whether additional course content was found and appended.
    """
    has_context = False
    extra_context = ""

    # 1. Try RAG: search uploaded documents in Milvus
    rag_context = query_knowledge_base(user_question, chapter_id=chapter_id)
    if rag_context:
        extra_context = (
            "以下是从课程资料库中检索到的与当前问题相关的内容，请优先参考：\n\n"
            + rag_context
            + "\n\n请基于上述资料回答学生的问题。如果资料不足以完整回答，"
            "可以结合你的知识进行补充，但请说明哪些是资料中的内容、哪些是补充说明。"
        )
        has_context = True

    # 2. Fallback: if no documents uploaded, use chapter descriptions from DB
    else:
        from app.models.chapter import Chapter
        chapters = (
            db.query(Chapter)
            .filter(Chapter.is_active == True)
            .order_by(Chapter.order_index.asc())
            .all()
        )
        if chapters:
            chapter_lines = []
            target_chapter = None
            for ch in chapters:
                if chapter_id and ch.id == chapter_id:
                    target_chapter = ch
                if ch.description:
                    chapter_lines.append(f"- **{ch.title}**：{ch.description}")

            if target_chapter and target_chapter.description:
                extra_context = (
                    f"用户当前正在学习「{target_chapter.title}」章节。\n\n"
                    "以下是本课程各章节的概要介绍，供参考：\n\n"
                    + "\n".join(chapter_lines)
                    + "\n\n请结合软件工程课程知识回答学生的问题。"
                )
            else:
                extra_context = (
                    "以下是本课程各章节的概要介绍：\n\n"
                    + "\n".join(chapter_lines)
                    + "\n\n请结合软件工程课程知识回答学生的问题。"
                )
            has_context = True

    if not has_context:
        return LEARNING_ASSISTANT_PROMPT, False

    return (
        LEARNING_ASSISTANT_PROMPT
        + "\n\n## 课程参考资料\n"
        + extra_context
    ), True


# ── Session CRUD ──────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse)
def create_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=data.title or "新对话",
        chapter_id=data.chapter_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse.model_validate(session)


@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List current user's chat sessions."""
    sessions = (
        db.query(ChatSession)
        .filter(
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True,
        )
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [SessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_messages(
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chat history for a session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [MessageResponse.model_validate(m) for m in messages]


@router.put("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int,
    data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a chat session (rename)."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")
    if data.title is not None:
        session.title = data.title
    db.commit()
    db.refresh(session)
    return SessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a chat session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")
    session.is_active = False
    db.commit()
    return {"message": "对话已删除"}


# ── Message sending with RAG-enhanced streaming ───────────────────────

@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: int,
    data: MessageSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get SSE streaming response with RAG enhancement."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="对话不存在")

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=data.content,
    )
    db.add(user_msg)

    # Auto-title: use first 15 chars of the very first user message
    if session.message_count == 0:
        title = data.content.strip()[:15]
        if title:
            session.title = title

    db.commit()

    # Update session timestamp
    session.message_count += 1
    db.commit()

    # Get LLM config (model name only; api_key comes from system env)
    llm_config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
    model = llm_config.model_name if llm_config else settings.LLM_MODEL
    provider = llm_config.provider if llm_config else "dashscope"
    base_url = llm_config.base_url if llm_config else None
    api_key = llm_config.api_key if llm_config and llm_config.api_key else None

    # Build chat history (last 20 messages, excluding the current user message)
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
        .all()
    )

    # Build the message array for the LLM:
    #   1. System message (base prompt + optional RAG / chapter context)
    #   2. Previous conversation history (assistant & user turns)
    #   3. Current user question
    system_content, has_context = _build_system_message(
        db, data.content, chapter_id=data.chapter_id
    )
    messages_for_llm = [{"role": "system", "content": system_content}]

    for msg in history[:-1]:  # exclude the just-saved user message
        messages_for_llm.append({
            "role": msg.role,
            "content": msg.content,
        })

    messages_for_llm.append({"role": "user", "content": data.content})

    async def generate():
        full_response = ""
        # Separate DB session for the generator to avoid lifecycle issues
        local_db = SessionLocal()
        try:
            # Notify the frontend about context status
            if has_context:
                yield f"data: {json.dumps({'type': 'context', 'content': '已检索到相关课程内容，正在生成回答...'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'context', 'content': '未找到相关课程资料，基于通用知识回答'})}\n\n"

            # Stream response from LLM
            async for chunk in stream_chat(
                messages=messages_for_llm,
                model=model,
                provider=provider,
                base_url=base_url,
                api_key=api_key,
            ):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # Resource recommendation
            try:
                recs = recommend_resources(
                    question=data.content,
                    answer=full_response,
                    chapter_id=data.chapter_id or session.chapter_id,
                    top_k=5,
                    max_results=3,
                )
                if recs:
                    yield f"data: {json.dumps({'type': 'recommendation', 'content': recs})}\n\n"
            except Exception as rec_err:
                logger.warning(f"Recommendation failed: {rec_err}")

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'抱歉，发生错误: {str(e)}'})}\n\n"
        finally:
            if full_response:
                try:
                    assistant_msg = ChatMessage(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                    )
                    local_db.add(assistant_msg)
                    local_db.commit()
                except Exception:
                    pass
            local_db.close()
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
