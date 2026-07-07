"""Mixture of Agents (MoA) — fan out to N models, aggregate responses."""

from __future__ import annotations

import asyncio
import logging

from apps.agent_runtime.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

DEFAULT_MODELS = ["qwen3:8b", "qwen3:14b", "gemma3:12b"]


async def _query_model(
    client: LLMClient,
    model: str,
    messages: list[dict],
) -> str:
    """Query a single model and return its response."""
    try:
        resp = await client.chat(messages=messages, model=model, temperature=0.7)
        return resp.content if hasattr(resp, "content") else str(resp)
    except Exception as e:
        logger.warning(f"MoA model {model} failed: {e}")
        return ""


async def moa_generate(
    client: LLMClient,
    prompt: str,
    models: list[str] | None = None,
    aggregator_model: str = "qwen3:8b",
    context: str = "",
) -> LLMResponse:
    """Generate a response using Mixture of Agents.

    1. Fan out prompt to N models in parallel
    2. Collect all responses
    3. Aggregate via a final LLM call
    """
    models = models or DEFAULT_MODELS
    messages: list[dict] = [
        {"role": "system", "content": "You are a helpful assistant. Answer the user's question."},
    ]
    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    logger.info(f"MoA: querying {len(models)} models in parallel")

    tasks = [_query_model(client, model, messages) for model in models]
    responses = await asyncio.gather(*tasks)

    candidate_responses = [
        f"### {model}\n{resp}"
        for model, resp in zip(models, responses)
        if resp.strip()
    ]

    if not candidate_responses:
        return LLMResponse(content="All models failed to respond.", model=aggregator_model)

    if len(candidate_responses) == 1:
        return LLMResponse(content=responses[0], model=models[0])

    aggregation_prompt = (
        "You have received multiple candidate responses to the same question.\n"
        "Synthesize the best elements into a single, high-quality answer.\n"
        "Be concise and accurate.\n\n"
        "Candidates:\n\n" + "\n\n".join(candidate_responses)
    )

    agg_messages = [
        {"role": "system", "content": "You are an expert editor. Synthesize multiple responses into one best answer."},
        {"role": "user", "content": aggregation_prompt},
    ]

    agg_resp = await client.chat(messages=agg_messages, model=aggregator_model, temperature=0.3)

    return LLMResponse(
        content=agg_resp.content if hasattr(agg_resp, "content") else str(agg_resp),
        model=aggregator_model,
    )
