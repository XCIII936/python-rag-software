"""RAG pipeline: knowledge base search and embedding generation.

Searches Milvus for relevant document chunks and provides
a formatted context string for LLM prompts.
"""

import logging
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger("course_agent.rag")


def _get_milvus_collection() -> Optional["Milvus"]:
    """Get the LangChain Milvus vectorstore wrapper.

    Returns None if Milvus is not available.
    """
    try:
        from langchain_milvus import Milvus as LangChainMilvus
        from langchain_community.embeddings import FakeEmbeddings
        from pymilvus import connections

        # Try connecting to Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            timeout=5,
        )

        # Use a simple embedding function — in production this would be
        # the DashScope embedding model wrapped in a LangChain embedder.
        # For now we use FakeEmbeddings so that the vectorstore is available
        # even without a live embedding API.
        embeddings = FakeEmbeddings(size=768)

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
        logger.warning(
            "Milvus is not available, RAG search disabled. "
            "Install pymilvus and ensure Milvus is running. "
            f"Error: {exc}"
        )
        return None


def query_knowledge_base(
    question: str,
    chapter_id: Optional[int] = None,
    top_k: int = 5,
) -> str:
    """Search the knowledge base for chunks relevant to the question.

    Args:
        question: The user's question.
        chapter_id: Optional chapter ID to narrow the search.
        top_k: Number of results to return.

    Returns:
        A formatted context string, or an empty string if unavailable.
    """
    vectorstore = _get_milvus_collection()
    if vectorstore is None:
        return ""

    try:
        # Build search filter if chapter_id is provided
        search_expr = None
        if chapter_id is not None:
            search_expr = f"chapter_id == {chapter_id}"

        docs = vectorstore.similarity_search(
            query=question,
            k=top_k,
            expr=search_expr,
        )

        if not docs:
            return ""

        # Format results into a readable context string
        lines = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知来源")
            page = doc.metadata.get("page", "")
            chunk_title = doc.metadata.get("title", "")
            source_info = f"[{source}"
            if page:
                source_info += f" - 第{page}页"
            if chunk_title:
                source_info += f" - {chunk_title}"
            source_info += "]"

            lines.append(f"{source_info}\n{doc.page_content}\n")

        return "\n".join(lines)

    except Exception as exc:
        logger.error(f"RAG search failed: {exc}")
        return ""


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Batch-generate embeddings for a list of texts.

    Uses the DashScope embedding API. Returns a list of embedding vectors
    where each vector is a list of floats.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    from app.services.llm.dashscope_client import get_embedding

    embeddings = []
    for text in texts:
        try:
            vec = get_embedding(text)
            embeddings.append(vec)
        except Exception as exc:
            logger.error(f"Failed to generate embedding: {exc}")
            embeddings.append([])
    return embeddings
