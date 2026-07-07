"""Chat handler with RAG augmentation."""

from __future__ import annotations

import logging

from apps.agent_runtime import rag as rag_module
from apps.agent_runtime.llm_client import LLMClient

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = (
    "You are Spark AI, a creative media production assistant.\n"
    "You are integrated into the Spark Media Workstation, which provides:\n"
    "- Image generation (FLUX models)\n"
    "- Video generation (LTX-Video)\n"
    "- Text-to-speech (F5-TTS)\n"
    "- Music generation\n"
    "- 3D asset generation\n"
    "- RAG memory from uploaded documents\n"
    "- Web research agent\n"
    "- Coding agent\n\n"
    "Answer questions helpfully and concisely."
)


async def handle_chat(
    client: LLMClient,
    message: str,
    model: str = "qwen3:8b",
    context: str = "Default",
    history: list[dict] | None = None,
    active_contexts: list[str] | None = None,
    images: list[str] | None = None,
) -> str:
    """Handle a plain chat message via LLM with optional RAG augmentation."""
    system = CHAT_SYSTEM_PROMPT.replace("Default", context)

    # RAG augmentation
    try:
        hits = await rag_module.query(message, limit=3)
        if hits:
            segments = [f"[Source: {h['source']}] (Score: {h['score']:.2f}):\n{h['text']}" for h in hits]
            rag_context = "\n\n".join(segments)
            system += (
                "\n\nUse the following reference context from uploaded documents if relevant:\n"
                f"{rag_context}"
            )
    except Exception as e:
        logger.warning(f"RAG query failed: {e}")

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        for h in history[-10:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

    user_msg: dict = {"role": "user", "content": message}
    if images:
        user_msg["images"] = images
    messages.append(user_msg)

    response = await client.chat(messages=messages, model=model, temperature=0.7)
    return response.content
