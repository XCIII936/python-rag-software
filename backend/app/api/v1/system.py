"""System management API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.core.config import settings
from app.models.user import User
from app.models.chapter import Chapter
from app.models.document import KnowledgeBaseDocument
from app.models.assessment import AssessmentRecord
from app.models.chat import ChatSession
from app.models.log import SystemLog
from app.models.llm_config import LlmConfig
from app.schemas.system import (
    LlmConfigUpdate,
    LlmConfigResponse,
    DashboardStats,
    ActivityItem,
    LogResponse,
)
from app.utils.logger import log_info

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics with recent activity."""
    # Recent activity from system logs
    recent_logs = (
        db.query(SystemLog)
        .order_by(SystemLog.created_at.desc())
        .limit(10)
        .all()
    )
    activity = []
    for log in recent_logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        activity.append(ActivityItem(
            id=log.id,
            username=user.username if user else "",
            action=log.action or "",
            module=log.module or "",
            detail=log.message or "",
            created_at=log.created_at,
        ))

    return DashboardStats(
        total_students=db.query(User).filter(User.role == "student").count(),
        total_chapters=db.query(Chapter).filter(Chapter.is_active == True).count(),
        total_documents=db.query(KnowledgeBaseDocument).count(),
        total_assessments=db.query(AssessmentRecord).count(),
        total_chat_sessions=db.query(ChatSession).count(),
        recent_activity=activity,
    )


@router.get("/llm-config", response_model=LlmConfigResponse)
def get_llm_config(
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Get current LLM configuration."""
    config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
    if not config:
        # Return default config
        return LlmConfigResponse(
            id=0,
            provider="dashscope",
            model_name=settings.LLM_MODEL,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            embedding_model=settings.EMBEDDING_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            top_p=0.9,
            is_active=True,
        )
    return LlmConfigResponse.model_validate(config)


@router.put("/llm-config", response_model=LlmConfigResponse)
def update_llm_config(
    data: LlmConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """Update LLM configuration (teacher only)."""
    config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
    if not config:
        config = LlmConfig(is_active=True)
        db.add(config)
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(config, key, value)
    config.updated_by = current_user.id
    db.commit()
    db.refresh(config)
    log_info("system", "LLM 配置已更新", user_id=current_user.id)
    return LlmConfigResponse.model_validate(config)


@router.post("/llm-config/test")
def test_llm_connection(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """Test LLM API connection using the system API key."""
    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="未配置 API Key（请设置系统环境变量 ali-qwen3-max-api）")
    # Simple test - will be expanded with actual LLM call
    return {"message": "连接测试已发送", "status": "checking"}


@router.get("/logs", response_model=dict)
def get_system_logs(
    level: Optional[str] = None,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_teacher),
):
    """Get system logs with pagination and filters (teacher only)."""
    query = db.query(
        SystemLog, User.username
    ).outerjoin(
        User, SystemLog.user_id == User.id
    )

    if level:
        query = query.filter(SystemLog.level == level.upper())
    if module:
        query = query.filter(SystemLog.module == module)
    if start_date:
        query = query.filter(SystemLog.created_at >= start_date)
    if end_date:
        query = query.filter(SystemLog.created_at <= f"{end_date} 23:59:59")

    total = query.count()
    results = (
        query.order_by(SystemLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for log_row, username in results:
        item = LogResponse.model_validate(log_row)
        item_dict = item.model_dump()
        item_dict["username"] = username or ""
        items.append(item_dict)

    return {
        "total": total,
        "items": items,
    }
