"""PDF parser using PyPDF2.

Extracts text page by page from PDF files and returns structured data
with page numbers and metadata.
"""

import logging
from typing import List, Dict, Any

import PyPDF2

logger = logging.getLogger("course_agent.document_parse.pdf")


def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract text from a PDF file page by page.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        A list of dicts, each containing:
            - page_num (int): 1-based page number.
            - content (str): Extracted text from the page.
            - metadata (dict): File-level metadata (title, author, etc.).

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        PyPDF2.errors.PdfReadError: If the PDF is corrupted.
    """
    results: List[Dict[str, Any]] = []

    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)

        # Collect file-level metadata
        doc_metadata = {}
        if reader.metadata:
            for key in reader.metadata:
                # PyPDF2 stores keys as '/' + name
                clean_key = key.lstrip("/")
                doc_metadata[clean_key] = str(reader.metadata[key])

        total_pages = len(reader.pages)
        logger.info(f"Parsing PDF: {file_path}, {total_pages} pages")

        for page_num in range(total_pages):
            try:
                page = reader.pages[page_num]
                text = page.extract_text()

                # Clean up whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                cleaned_text = "\n".join(lines)

                results.append({
                    "page_num": page_num + 1,
                    "content": cleaned_text or "",
                    "metadata": {
                        **doc_metadata,
                        "total_pages": total_pages,
                        "file_path": file_path,
                    },
                })
            except Exception as exc:
                logger.warning(f"Failed to extract page {page_num + 1}: {exc}")
                results.append({
                    "page_num": page_num + 1,
                    "content": "",
                    "metadata": {
                        "error": str(exc),
                        "total_pages": total_pages,
                        "file_path": file_path,
                    },
                })

    return results
