"""Chat CRUD operations."""

from typing import List
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.chat import ChatSession, ChatMessage


class CRUDChatSession(CRUDBase[ChatSession, None, None]):
    def get_user_sessions(self, db: Session, user_id: int) -> List[ChatSession]:
        return (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id, ChatSession.is_active == True)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )


class CRUDChatMessage:
    def get_session_messages(
        self, db: Session, session_id: int, skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self, db: Session, *, session_id: int, role: str, content: str, **kwargs
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id, role=role, content=content, **kwargs
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg


chat_session_crud = CRUDChatSession(ChatSession)
chat_message_crud = CRUDChatMessage()
