"""Multi-provider LLM client with native tool-calling support.
Supports Ollama (primary) and vLLM (fallback)."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

RETRY_ATTEMPTS = 3
RETRY_DELAYS = [2, 4, 8]


class LLMError(Exception):
    pass


class LLMResponse:
    """Normalized response from any provider."""

    def __init__(
        self,
        content: str = "",
        tool_calls: list[dict] | None = None,
        tokens_used: int = 0,
        model: str = "",
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.tokens_used = tokens_used
        self.model = model


class LLMClient:
    """Multi-provider LLM client. Prefers Ollama native tool-calling,
    falls back to vLLM OpenAI-compatible API."""

    def __init__(self, ollama_url: str, vllm_url: str | None = None):
        self.ollama_url = ollama_url.rstrip("/")
        self.vllm_url = (vllm_url or "").rstrip("/") if vllm_url else None

    async def chat(
        self,
        messages: list[dict],
        model: str = "qwen3:8b",
        tools: list[dict] | None = None,
        stream: bool = False,
        timeout: int = 120,
        temperature: float = 0.7,
    ) -> LLMResponse | AsyncGenerator[dict, None]:
        """Send chat completion request. Uses Ollama native tool-calling."""
        if stream:
            return self._stream(messages, model, tools, timeout, temperature)

        payload = self._build_ollama_payload(messages, model, tools, temperature)

        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        f"{self.ollama_url}/api/chat", json=payload
                    )
                    resp.raise_for_status()
                    data = resp.json()
                return self._parse_ollama_response(data, model)
            except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as exc:
                if attempt < RETRY_ATTEMPTS - 1:
                    import asyncio
                    delay = RETRY_DELAYS[attempt]
                    logger.warning("LLM request failed (%s), retrying in %ds", exc, delay)
                    await asyncio.sleep(delay)
                else:
                    raise LLMError(f"All {RETRY_ATTEMPTS} attempts failed: {exc}") from exc

    async def _stream(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None,
        timeout: int,
        temperature: float,
    ) -> AsyncGenerator[dict, None]:
        payload = self._build_ollama_payload(messages, model, tools, temperature, stream=True)

        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST", f"{self.ollama_url}/api/chat", json=payload
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")
                            done = chunk.get("done", False)
                            tool_calls = chunk.get("message", {}).get("tool_calls", [])
                            yield {
                                "token": token,
                                "done": done,
                                "tool_calls": tool_calls,
                            }
                return
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                if attempt < RETRY_ATTEMPTS - 1:
                    import asyncio
                    delay = RETRY_DELAYS[attempt]
                    logger.warning("LLM stream failed (%s), retrying in %ds", exc, delay)
                    await asyncio.sleep(delay)
                else:
                    raise LLMError(f"Stream failed after {RETRY_ATTEMPTS} attempts: {exc}") from exc

    def _build_ollama_payload(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None,
        temperature: float,
        stream: bool = False,
    ) -> dict:
        # Strip images from non-vision models to prevent 400 errors
        vision_models = {"llava", "llama3.2-vision", "minicpm-v", "gemma4"}
        is_vision = any(vm in model.lower() for vm in vision_models)

        cleaned_messages = []
        for msg in messages:
            cleaned = dict(msg)
            if not is_vision and "images" in cleaned:
                # Remove images for non-vision models
                cleaned = {k: v for k, v in cleaned.items() if k != "images"}
                if cleaned.get("content"):
                    cleaned["content"] += "\n\n[Note: An image was attached but this model cannot process images.]"
            cleaned_messages.append(cleaned)

        payload: dict = {
            "model": model,
            "messages": cleaned_messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": 0.95,
            },
        }
        if tools:
            payload["tools"] = tools
        return payload

    def _parse_ollama_response(self, data: dict, model: str) -> LLMResponse:
        msg = data.get("message", {})
        content = msg.get("content", "")
        raw_tool_calls = msg.get("tool_calls", [])

        tool_calls = []
        for tc in raw_tool_calls:
            func = tc.get("function", {})
            tool_calls.append({
                "name": func.get("name", ""),
                "arguments": func.get("arguments", {}),
            })

        tokens_used = self._estimate_tokens(content)
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            tokens_used=tokens_used,
            model=model,
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return len(text) // 4
