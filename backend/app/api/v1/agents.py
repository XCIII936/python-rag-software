"""Agent configuration API routes."""

import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.user import User
from app.models.agent import AgentConfig
from app.models.llm_config import LlmConfig
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentInvokeRequest
from app.services.llm.dashscope_client import stream_chat
from app.utils.logger import log_info

logger = logging.getLogger("course_agent.agents")

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agent configurations."""
    agents = db.query(AgentConfig).order_by(AgentConfig.created_at.desc()).all()
    return [AgentResponse.model_validate(a) for a in agents]


@router.post("", response_model=AgentResponse)
def create_agent(
    data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """Create a new agent config (teacher only)."""
    agent = AgentConfig(**data.model_dump(), created_by=current_user.id)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    log_info("agent", f"创建智能体: {agent.name}")
    return AgentResponse.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get agent detail."""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return AgentResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Update agent config (teacher only)."""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    db.commit()
    db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}")
def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Delete agent config (teacher only)."""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    db.delete(agent)
    db.commit()
    return {"message": "智能体已删除"}


@router.post("/{agent_id}/invoke")
async def invoke_agent(
    agent_id: int,
    data: AgentInvokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invoke an agent with SSE streaming response.

    Uses the agent's system prompt and the active LLM config to
    generate a streaming response.
    """
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    if not agent.is_active:
        raise HTTPException(status_code=400, detail="智能体已停用")

    # Get active LLM config for provider selection
    llm_config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
    model = llm_config.model_name if llm_config else "qwen3-max"
    provider = llm_config.provider if llm_config else "dashscope"
    base_url = llm_config.base_url if llm_config else None

    # Build messages: system prompt (agent) + user message
    system_prompt = agent.system_prompt or "你是一个有帮助的智能体。"
    messages_for_llm = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": data.message},
    ]

    async def generate():
        full_response = ""
        try:
            async for chunk in stream_chat(
                messages=messages_for_llm,
                model=model,
                provider=provider,
                base_url=base_url,
            ):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

        except Exception as e:
            logger.error(f"Agent invoke failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'抱歉，发生错误: {str(e)}'})}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
