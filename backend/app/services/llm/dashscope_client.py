"""LLM client supporting DashScope (Qwen) and OpenAI-compatible APIs (DeepSeek, etc.).

Supports streaming chat, synchronous chat, and text embeddings.
Falls back to settings.DASHSCOPE_API_KEY when no key is provided.
For OpenAI-compatible providers (DeepSeek etc.), uses httpx for HTTP streaming.
"""

import json
from typing import AsyncGenerator, List, Optional

import dashscope
from http import HTTPStatus
import httpx

from app.core.config import settings


def _resolve_api_key(api_key: Optional[str] = None) -> str:
    """Return the given key or fall back to the global setting."""
    return api_key or settings.DASHSCOPE_API_KEY or ""


async def stream_chat(
    messages: List[dict],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream chat completion from the configured LLM provider.

    Supports:
    - DashScope (Qwen) via native SDK
    - OpenAI-compatible APIs (DeepSeek, etc.) via httpx

    Args:
        messages: List of dicts with 'role' and 'content' keys.
        api_key: Optional API key; falls back to settings.
        model: Model name; falls back to settings.LLM_MODEL.
        provider: Provider type ('dashscope' or 'openai').
        base_url: API base URL for OpenAI-compatible providers.

    Yields:
        Text chunks as they are generated.
    """
    key = _resolve_api_key(api_key)
    model_name = model or settings.LLM_MODEL
    provider = (provider or "dashscope").lower()

    if not key:
        yield "【错误】未配置 API Key，请在系统设置中配置。"
        return

    # Normalise aliases
    # "bailian" = Alibaba Cloud Bailian compatible mode → OpenAI path
    if provider == "bailian":
        provider = "openai"
        if not base_url:
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ── DashScope native SDK path ──
    if provider == "dashscope":
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

    # ── OpenAI-compatible API path (DeepSeek, etc.) ──
    else:
        # Build the API endpoint URL
        if base_url:
            url = base_url.rstrip("/")
            if not url.endswith("/chat/completions"):
                url += "/chat/completions"
        else:
            url = "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST", url, json=payload, headers=headers
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        yield (
                            f"【错误】HTTP {response.status_code}: "
                            f"{error_body.decode('utf-8', errors='replace')}"
                        )
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except httpx.TimeoutException:
            yield "【错误】API 请求超时，请稍后重试。"
        except httpx.RequestError as exc:
            yield f"【错误】网络请求失败: {exc}"


def chat(
    messages: List[dict],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
) -> str:
    """Synchronous non-streaming chat completion.

    Suitable for assessment and report generation where the full response
    is needed at once.

    Args:
        messages: List of dicts with 'role' and 'content' keys.
        api_key: Optional API key; falls back to settings.
        model: Model name; falls back to settings.LLM_MODEL.
        provider: Provider type ('dashscope' or 'openai').
        base_url: API base URL for OpenAI-compatible providers.

    Returns:
        The full response text.
    """
    key = _resolve_api_key(api_key)
    model_name = model or settings.LLM_MODEL
    provider = (provider or "dashscope").lower()

    if not key:
        return "【错误】未配置 API Key，请在系统设置中配置。"

    # Normalise aliases
    if provider == "bailian":
        provider = "openai"
        if not base_url:
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # ── DashScope native SDK path ──
    if provider == "dashscope":
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
            raise RuntimeError(
                f"DashScope API error {response.code}: {response.message}"
            )

    # ── OpenAI-compatible API path ──
    else:
        if base_url:
            url = base_url.rstrip("/")
            if not url.endswith("/chat/completions"):
                url += "/chat/completions"
        else:
            url = "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"API error {resp.status_code}: {resp.text}"
                    )
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except httpx.TimeoutException:
            raise RuntimeError("API 请求超时，请稍后重试。")
        except httpx.RequestError as exc:
            raise RuntimeError(f"网络请求失败: {exc}")


def get_embedding(text: str, api_key: Optional[str] = None) -> List[float]:
    """Get text embedding vector using DashScope text-embedding-v3.

    Args:
        text: Input text to embed.
        api_key: Optional API key; falls back to settings.

    Returns:
        A list of floats representing the embedding vector.
    """
    key = _resolve_api_key(api_key)
    if not key:
        raise ValueError("未配置 API Key，无法生成向量。")

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
