"""LLM client wrapping the DashScope (Qwen) API.

Supports streaming chat, synchronous chat, and text embeddings.
Falls back to settings.DASHSCOPE_API_KEY when no key is provided.
"""

import json
from typing import AsyncGenerator, List, Optional

import dashscope
from http import HTTPStatus

from app.core.config import settings


def _resolve_api_key(api_key: Optional[str] = None) -> str:
    """Return the given key or fall back to the global setting."""
    return api_key or settings.DASHSCOPE_API_KEY or ""


async def stream_chat(
    messages: List[dict],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream chat completion from DashScope.

    Args:
        messages: List of dicts with 'role' and 'content' keys.
        api_key: Optional API key; falls back to settings.
        model: Model name; falls back to settings.LLM_MODEL.

    Yields:
        Text chunks as they are generated.
    """
    key = _resolve_api_key(api_key)
    model_name = model or settings.LLM_MODEL

    if not key:
        yield "【错误】未配置 DashScope API Key，请在系统设置中配置。"
        return

    dashscope.api_key = key

    responses = dashscope.Generation.call(
        model=model_name,
        messages=messages,
        stream=True,
        incremental_output=True,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        result_format="message",
    )

    for response in responses:
        if response.status_code == HTTPStatus.OK:
            if response.output and response.output.choices:
                choice = response.output.choices[0]
                delta = choice.get("message", {}).get("content", "")
                if delta:
                    yield delta
        else:
            yield f"【错误】{response.code}: {response.message}"
            return


def chat(
    messages: List[dict],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Synchronous non-streaming chat completion.

    Suitable for assessment and report generation where the full response
    is needed at once.

    Args:
        messages: List of dicts with 'role' and 'content' keys.
        api_key: Optional API key; falls back to settings.
        model: Model name; falls back to settings.LLM_MODEL.

    Returns:
        The full response text.
    """
    key = _resolve_api_key(api_key)
    model_name = model or settings.LLM_MODEL

    if not key:
        return "【错误】未配置 DashScope API Key，请在系统设置中配置。"

    dashscope.api_key = key

    response = dashscope.Generation.call(
        model=model_name,
        messages=messages,
        stream=False,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        result_format="message",
    )

    if response.status_code == HTTPStatus.OK:
        if response.output and response.output.choices:
            return response.output.choices[0].get("message", {}).get("content", "")
        return ""
    else:
        raise RuntimeError(f"DashScope API error {response.code}: {response.message}")


def get_embedding(text: str, api_key: Optional[str] = None) -> List[float]:
    """Get text embedding vector using text-embedding-v3.

    Args:
        text: Input text to embed.
        api_key: Optional API key; falls back to settings.

    Returns:
        A list of floats representing the embedding vector.
    """
    key = _resolve_api_key(api_key)
    if not key:
        raise ValueError("未配置 DashScope API Key，无法生成向量。")

    dashscope.api_key = key

    response = dashscope.TextEmbedding.call(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )

    if response.status_code == HTTPStatus.OK:
        if response.output and response.output.embeddings:
            return response.output.embeddings[0].get("embedding", [])
        return []
    else:
        raise RuntimeError(
            f"DashScope embedding error {response.code}: {response.message}"
        )
