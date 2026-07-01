"""Agent configuration API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.user import User
from app.models.agent import AgentConfig
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.utils.logger import log_info

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
