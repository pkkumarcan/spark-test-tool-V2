"""Chat routes: /api/text/chat, /api/text/enhance, /api/text/models."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from apps.agent_runtime.chat import handle_chat
from apps.agent_runtime.llm_client import LLMClient
from apps.agent_runtime.session import add_message, create_session
from apps.gateway.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/text")


class TextChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    model: str | None = None
    context: str = "Default"
    history: list[dict] | None = None
    images: list[str] | None = None
    active_contexts: list[str] | None = None


class TextEnhanceRequest(BaseModel):
    text: str
    style: str = "professional"
    model: str | None = None


@router.post("/chat")
async def text_chat(req: TextChatRequest):
    """Plain chat endpoint. Returns a text response."""
    model = req.model or settings.default_model
    session_id = req.session_id

    if not session_id:
        session = await create_session(settings.postgres_url, kind="chat")
        session_id = str(session["id"])

    await add_message(settings.postgres_url, session_id, "user", req.message)

    client = LLMClient(ollama_url=settings.ollama_base_url)
    response_text = await handle_chat(
        client=client,
        message=req.message,
        model=model,
        context=req.context,
        history=req.history,
        active_contexts=req.active_contexts,
        images=req.images,
    )

    await add_message(settings.postgres_url, session_id, "assistant", response_text)

    return {
        "session_id": session_id,
        "response": response_text,
        "model": model,
    }


@router.post("/enhance")
async def text_enhance(req: TextEnhanceRequest):
    """Enhance/rewrite text using LLM."""
    model = req.model or settings.default_model
    client = LLMClient(ollama_url=settings.ollama_base_url)

    system_prompt = (
        "You are an expert text enhancer. Rewrite the provided text to improve "
        "clarity, grammar, and style. Output ONLY the enhanced text."
    )
    resp = await client.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Style: {req.style}\n\nText:\n{req.text}"},
        ],
        model=model,
    )
    return {"enhanced_text": resp}


@router.get("/models")
async def list_models():
    """List available text models from Ollama."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            if r.status_code == 200:
                data = r.json()
                models = [m["name"] for m in data.get("models", [])]
                return {"models": models}
    except Exception as e:
        logger.warning(f"Failed to list Ollama models: {e}")
    return {"models": []}
