"""Token compression and context management."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MAX_CHARS_PER_TOKEN = 4
DEFAULT_MAX_TOKENS = 32000


def estimate_tokens(text: str) -> int:
    return len(text) // MAX_CHARS_PER_TOKEN


def compress_messages(
    messages: list[dict],
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[dict]:
    """Truncate older messages when context grows too large.
    Keeps system prompt + recent messages within budget."""
    total = sum(estimate_tokens(m.get("content", "")) for m in messages)
    if total <= max_tokens:
        return messages

    system = [m for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]

    system_tokens = sum(estimate_tokens(m.get("content", "")) for m in system)
    budget = max_tokens - system_tokens - 2000

    if budget <= 0:
        return system + rest[-2:]

    kept: list[dict] = []
    used = 0
    for msg in reversed(rest):
        t = estimate_tokens(msg.get("content", ""))
        if used + t > budget:
            break
        kept.insert(0, msg)
        used += t

    if kept and kept[0].get("role") == "user":
        skipped = len(rest) - len(kept)
        summary_msg = {
            "role": "user",
            "content": f"[{skipped} earlier messages compressed to save context. Continuing from here.]",
        }
        kept = [summary_msg] + kept

    return system + kept
