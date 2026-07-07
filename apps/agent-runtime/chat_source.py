"""Chat with uploaded sources — RAG-augmented chat with document context."""

from __future__ import annotations

import logging

from apps.agent_runtime import rag as rag_module
from apps.agent_runtime.llm_client import LLMClient

logger = logging.getLogger(__name__)

CHAT_SOURCE_PROMPT = (
    "You are Spark AI, a helpful research assistant.\n"
    "Answer the user's question based on the uploaded documents below.\n"
    "Cite sources when possible. If the documents don't contain the answer, say so."
)


async def chat_with_source(
    client: LLMClient,
    message: str,
    model: str = "qwen3:8b",
    history: list[dict] | None = None,
    source_filter: str | None = None,
) -> str:
    """Chat with RAG augmentation from uploaded documents.

    Args:
        client: LLM client instance.
        message: User's question.
        model: Model name.
        history: Chat history.
        source_filter: Optional filename/source filter for RAG queries.
    """
    rag_hits = []
    try:
        rag_hits = await rag_module.query(message, limit=5)
    except Exception as e:
        logger.warning(f"RAG query failed: {e}")

    if source_filter:
        rag_hits = [h for h in rag_hits if source_filter.lower() in h.get("source", "").lower()]

    system = CHAT_SOURCE_PROMPT
    if rag_hits:
        sources_block = "\n\n".join(
            f"[Source: {h['source']}] (relevance: {h['score']:.2f}):\n{h['text']}"
            for h in rag_hits
        )
        system += f"\n\n=== UPLOADED DOCUMENTS ===\n{sources_block}"

    messages: list[dict] = [{"role": "system", "content": system}]
    if history:
        for h in history[-10:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})

    response = await client.chat(messages=messages, model=model, temperature=0.7)
    return response.content
