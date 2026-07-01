"""Chinese-aware text splitter using LangChain's RecursiveCharacterTextSplitter.

Splits long documents into manageable chunks with configurable overlap,
using Chinese-specific separators for better boundary detection.
"""

from typing import List, Optional, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter


# Chinese-aware separators prioritised for semantic boundaries
_CHINESE_SEPARATORS = [
    "\n\n",      # Paragraph break
    "\n",        # Line break
    "。",        # Chinese full stop / period
    "；",        # Chinese semicolon
    "，",        # Chinese comma
    " ",         # Space
    "",          # Character-level fallback
]


def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[str]:
    """Split text into chunks using Chinese-aware separators.

    Args:
        text: The input text to split.
        chunk_size: Maximum characters per chunk (default 500).
        chunk_overlap: Overlap between chunks (default 50).

    Returns:
        A list of text chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        separators=_CHINESE_SEPARATORS,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)


def split_document(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Dict[str, Any]]:
    """Split a document and return chunks with metadata.

    Each returned dict contains:
        - content: the text chunk
        - metadata: the original metadata dict enriched with chunk_index

    Args:
        text: The input text to split.
        metadata: Optional metadata dict to attach to each chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        A list of dicts with 'content' and 'metadata' keys.
    """
    metadata = metadata or {}
    chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    result = []
    for i, chunk in enumerate(chunks):
        chunk_metadata = dict(metadata)
        chunk_metadata["chunk_index"] = i
        result.append({
            "content": chunk,
            "metadata": chunk_metadata,
        })

    return result
