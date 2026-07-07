"""Intent routing via model's native tool choice.
Uses the LLM's tool-calling capability to decide whether to use a tool
or return a direct chat response. No separate classifier needed."""

from __future__ import annotations

import logging

from apps.agent_runtime.llm_client import LLMClient, LLMResponse
from packages.tool_registry import get_schemas

logger = logging.getLogger(__name__)

ROUTING_SYSTEM_PROMPT = """You are Spark Router, an AI dispatcher for a creative media production studio.

Given a user message, decide whether to:
1. Use a tool to fulfill the request (if a tool matches)
2. Respond directly with a chat message

If a tool matches the user's intent, call it with the appropriate arguments.
If no tool matches, respond directly as a helpful assistant.

Be concise. When responding directly, keep answers brief and helpful."""


async def route_message(
    client: LLMClient,
    message: str,
    history: list[dict] | None = None,
    model: str = "qwen3:8b",
    images: list[str] | None = None,
) -> LLMResponse:
    """Route a user message through the LLM with native tool-calling.
    Returns an LLMResponse — if tool_calls is non-empty, the agent should
    execute those tools. Otherwise it's a direct chat response."""
    messages: list[dict] = [{"role": "system", "content": ROUTING_SYSTEM_PROMPT}]

    if history:
        for h in history[-8:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

    user_msg: dict = {"role": "user", "content": message}
    if images:
        user_msg["images"] = images
    messages.append(user_msg)

    tools = get_schemas()
    response = await client.chat(
        messages=messages,
        model=model,
        tools=tools if tools else None,
        temperature=0.3,
    )
    return response
