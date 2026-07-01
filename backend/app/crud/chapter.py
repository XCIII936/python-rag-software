"""Chapter CRUD operations."""

from app.crud.base import CRUDBase
from app.models.chapter import Chapter
from app.schemas.chapter import ChapterCreate, ChapterUpdate


class CRUDChapter(CRUDBase[Chapter, ChapterCreate, ChapterUpdate]):
    pass


chapter_crud = CRUDChapter(Chapter)
