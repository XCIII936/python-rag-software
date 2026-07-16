"""Resource recommendation service.

After a conversation turn, recommends relevant course materials
(video segments, slides, PDF pages) by searching the Milvus vector store.
"""

import json
import logging
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger("course_agent.recommendation")


class ResourceRecommendation:
    """A single recommended resource with metadata."""

    def __init__(
        self,
        title: str,
        resource_type: str,
        description: str = "",
        relevance_score: float = 0.0,
        source_info: Optional[dict] = None,
        chapter_id: Optional[int] = None,
        document_id: Optional[int] = None,
        chunk_id: Optional[str] = None,
    ):
        self.title = title
        self.resource_type = resource_type  # ppt_slide | pdf_page | chapter_section
        self.description = description
        self.relevance_score = relevance_score
        self.source_info = source_info or {}
        self.chapter_id = chapter_id
        self.document_id = document_id
        self.chunk_id = chunk_id

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "resource_type": self.resource_type,
            "description": self.description,
            "relevance_score": round(self.relevance_score, 2),
            "source_info": self.source_info,
        }


def recommend_resources(
    question: str,
    answer: str,
    chapter_id: Optional[int] = None,
    top_k: int = 5,
    max_results: int = 5,
) -> List[dict]:
    """Search the knowledge base for resources relevant to the conversation.

    1. Query Milvus for semantically similar document chunks.
    2. Group and deduplicate by document/source.
    3. Sort by relevance score.
    4. Return the top-N recommendations.

    Args:
        question: The user's original question.
        answer: The AI's generated answer (or the conversation summary).
        chapter_id: Optional chapter filter.
        top_k: Number of initial chunks to fetch from Milvus.
        max_results: Max recommendations to return.

    Returns:
        A list of recommendation dicts.
    """
    try:
        vectorstore = _get_vectorstore()
        if vectorstore is None:
            logger.warning("Milvus unavailable — cannot generate recommendations.")
            return []

        # Combine question + answer for a richer query
        combined_query = f"{question}\n{answer}" if answer else question

        search_expr = None
        if chapter_id is not None:
            search_expr = f"chapter_id == {chapter_id}"

        docs = vectorstore.similarity_search(
            query=combined_query,
            k=top_k,
            expr=search_expr,
        )

        if not docs:
            return _get_fallback_recommendations(chapter_id)

        # Deduplicate by source document
        seen_docs = set()
        recommendations = []
        for doc in docs:
            source = doc.metadata.get("source", "")
            if source in seen_docs:
                continue
            seen_docs.add(source)

            page = doc.metadata.get("page", "")
            file_type = doc.metadata.get("file_type", "")
            chunk_title = doc.metadata.get("title", "")

            # Determine resource type
            if file_type in ("ppt", "pptx"):
                resource_type = "ppt_slide"
            elif file_type in ("pdf",):
                resource_type = "pdf_page"
            elif file_type in ("doc", "docx"):
                resource_type = "document_section"
            elif file_type in ("md", "markdown"):
                resource_type = "markdown_section"
            else:
                resource_type = "chapter_section"

            # Build title
            title = chunk_title or source
            source_info = {"source": source}
            if page:
                source_info["page"] = page

            rec = ResourceRecommendation(
                title=title,
                resource_type=resource_type,
                description=doc.page_content[:200],
                relevance_score=1.0,  # Milvus doesn't return scores by default
                source_info=source_info,
                chapter_id=doc.metadata.get("chapter_id") or chapter_id,
                document_id=doc.metadata.get("document_id"),
                chunk_id=doc.metadata.get("chunk_id"),
            )
            recommendations.append(rec.to_dict())

            if len(recommendations) >= max_results:
                break

        return recommendations

    except Exception as exc:
        logger.error(f"Resource recommendation failed: {exc}")
        return []


def _get_vectorstore():
    """Get the LangChain Milvus vectorstore wrapper.

    Returns None if Milvus is not available.
    """
    try:
        from langchain_milvus import Milvus as LangChainMilvus
        from pymilvus import connections

        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            timeout=5,
        )

        from app.services.rag.rag_chain import DashScopeEmbeddings
        embeddings = DashScopeEmbeddings(api_key=settings.DASHSCOPE_API_KEY)

        vectorstore = LangChainMilvus(
            embedding_function=embeddings,
            collection_name=settings.MILVUS_COLLECTION,
            connection_args={
                "host": settings.MILVUS_HOST,
                "port": settings.MILVUS_PORT,
            },
        )
        return vectorstore

    except Exception as exc:
        logger.warning(f"Milvus connection failed for recommendations: {exc}")
        return None


def _get_fallback_recommendations(chapter_id: Optional[int] = None) -> List[dict]:
    """When Milvus is unavailable, return static suggestions based on chapter.

    These are generic fallback suggestions so the UI never appears empty.
    """
    if chapter_id:
        return [
            {
                "title": f"复习第 {chapter_id} 章课程资料",
                "resource_type": "chapter_section",
                "description": "请查看对应章节的课程文档和课件以加深理解。",
                "relevance_score": 0.5,
                "source_info": {"chapter_id": chapter_id},
            }
        ]
    return [
        {
            "title": "浏览课程章节",
            "resource_type": "chapter_section",
            "description": "前往「章节学习」查看所有课程章节和资料。",
            "relevance_score": 0.3,
            "source_info": {},
        }
    ]
