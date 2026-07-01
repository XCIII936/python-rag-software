"""Assessment CRUD operations."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.assessment import (
    ChapterAssessmentConfig,
    AssessmentRecord,
    AssessmentQuestion,
    AssessmentReport,
)


class CRUDConfig(CRUDBase[ChapterAssessmentConfig, None, None]):
    def get_by_chapter(self, db: Session, chapter_id: int) -> Optional[ChapterAssessmentConfig]:
        return (
            db.query(ChapterAssessmentConfig)
            .filter(ChapterAssessmentConfig.chapter_id == chapter_id)
            .first()
        )


class CRUDRecord(CRUDBase[AssessmentRecord, None, None]):
    def get_user_records(
        self, db: Session, user_id: int, chapter_id: Optional[int] = None
    ) -> List[AssessmentRecord]:
        query = db.query(AssessmentRecord).filter(
            AssessmentRecord.user_id == user_id
        )
        if chapter_id:
            query = query.filter(AssessmentRecord.chapter_id == chapter_id)
        return query.order_by(AssessmentRecord.created_at.desc()).all()

    def get_latest_by_chapter(
        self, db: Session, user_id: int, chapter_id: int
    ) -> Optional[AssessmentRecord]:
        return (
            db.query(AssessmentRecord)
            .filter(
                AssessmentRecord.user_id == user_id,
                AssessmentRecord.chapter_id == chapter_id,
                AssessmentRecord.status == "completed",
            )
            .order_by(AssessmentRecord.created_at.desc())
            .first()
        )


class CRUDQuestion(CRUDBase[AssessmentQuestion, None, None]):
    def get_by_record(self, db: Session, record_id: int) -> List[AssessmentQuestion]:
        return (
            db.query(AssessmentQuestion)
            .filter(AssessmentQuestion.record_id == record_id)
            .order_by(AssessmentQuestion.question_index.asc())
            .all()
        )


config_crud = CRUDConfig(ChapterAssessmentConfig)
record_crud = CRUDRecord(AssessmentRecord)
question_crud = CRUDQuestion(AssessmentQuestion)
