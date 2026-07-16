"""Markdown parser for course documents.

Splits markdown content into logical sections based on heading structure
(# ## ### etc.), preserving heading hierarchy so that each chunk can be
cited with its originating section title — similar in spirit to how the
PPT parser attaches a slide title to each slide's content.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("course_agent.document_parse.markdown")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def parse_markdown(file_path: str) -> List[Dict[str, Any]]:
    """Parse a Markdown (.md) file into sections split by headings.

    Args:
        file_path: Absolute or relative path to the .md file.

    Returns:
        A list of dicts, each containing:
            - section_index (int): 1-based section number.
            - heading (str): The heading text introducing this section
              (empty string if the section precedes the first heading).
            - heading_level (int): 1-6 (markdown '#' count), 0 if no heading.
            - content (str): The section's full text, including its
              heading line.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    lines = text.splitlines()
    sections: List[Dict[str, Any]] = []

    current_heading = ""
    current_level = 0
    current_lines: List[str] = []
    section_index = 0

    def flush() -> None:
        nonlocal section_index
        content = "\n".join(current_lines).strip()
        if content:
            section_index += 1
            sections.append({
                "section_index": section_index,
                "heading": current_heading,
                "heading_level": current_level,
                "content": content,
            })

    for line in lines:
        match = _HEADING_RE.match(line)
        if match:
            # A new heading starts a new section — flush the previous one.
            flush()
            current_lines = [line]
            current_level = len(match.group(1))
            current_heading = match.group(2).strip()
        else:
            current_lines.append(line)

    flush()

    if not sections:
        # No headings at all — treat the entire document as one section.
        content = text.strip()
        if content:
            sections.append({
                "section_index": 1,
                "heading": "",
                "heading_level": 0,
                "content": content,
            })

    logger.info(f"Parsed markdown: {file_path}, {len(sections)} sections")
    return sections
