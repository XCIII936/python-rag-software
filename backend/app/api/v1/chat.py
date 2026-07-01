"""Chat API routes with SSE streaming."""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import SessionCreate, SessionResponse, MessageSend, MessageResponse
from app.services.llm.dashscope_client import stream_chat
from app.services.rag.rag_chain import query_knowledge_base
from app.utils.logger import log_info

router = APIRouter()


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


@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: int,
    data: MessageSend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message and get SSE streaming response."""
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
    db.commit()

    # Update session timestamp
    session.message_count += 1
    db.commit()

    # Get LLM config
    from app.models.llm_config import LlmConfig
    llm_config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()

    # Build chat history context
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
        .all()
    )

    messages_for_llm = []
    for msg in history[:-1]:  # Exclude the current user message, already added
        messages_for_llm.append({
            "role": msg.role,
            "content": msg.content,
        })

    async def generate():
        full_response = ""
        try:
            # Search knowledge base for context
            context = query_knowledge_base(data.content, chapter_id=data.chapter_id)
            if context:
                context_text = "\n\n以下是与问题相关的课程资料:\n" + context
                messages_for_llm.append({"role": "system", "content": context_text})
                yield f"data: {json.dumps({'type': 'context', 'content': '已检索到相关课程资料'})}\n\n"

            messages_for_llm.append({"role": "user", "content": data.content})

            api_key = llm_config.api_key if llm_config else settings.DASHSCOPE_API_KEY
            model = llm_config.model_name if llm_config else settings.LLM_MODEL

            # Stream response from LLM
            async for chunk in stream_chat(
                messages=messages_for_llm,
                api_key=api_key,
                model=model,
            ):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # Resource recommendation
            yield f"data: {json.dumps({'type': 'recommendation', 'content': '基于您的提问，建议查看相关章节资料'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'抱歉，发生错误: {str(e)}'})}\n\n"
        finally:
            # Save assistant message
            if full_response:
                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                )
                db.add(assistant_msg)
                db.commit()
                session.message_count += 1
                db.commit()

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
