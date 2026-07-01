"""Document CRUD operations."""

from app.crud.base import CRUDBase
from app.models.document import KnowledgeBaseDocument
from app.schemas.document import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[KnowledgeBaseDocument, DocumentCreate, DocumentUpdate]):
    pass


document_crud = CRUDDocument(KnowledgeBaseDocument)
