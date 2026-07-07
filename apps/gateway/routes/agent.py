"""Agent routes: /api/orchestrator/code/* and /api/orchestrator/chat."""

from __future__ import annotations

import json
import logging
import os
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from apps.agent_runtime import rag as rag_module
from apps.agent_runtime.approval import approve_tool_call, reject_tool_call
from apps.agent_runtime.llm_client import LLMClient
from apps.agent_runtime.session import (
    add_message,
    create_session,
)
from apps.agent_runtime.state_machine import AgentStateMachine
from apps.gateway.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    model: str | None = None
    context: str = "Default"
    history: list[dict] | None = None
    images: list[str] | None = None


class AgentStreamRequest(BaseModel):
    task: str
    session_id: str | None = None
    model: str | None = None
    max_iterations: int = 15


def _get_llm_client() -> LLMClient:
    return LLMClient(ollama_url=settings.ollama_base_url)


@router.post("/chat")
async def orchestrator_chat(req: ChatRequest):
    """Route a chat message through the agent. Returns a routed response."""
    model = req.model or settings.default_model
    session_id = req.session_id

    if not session_id:
        session = await create_session(settings.postgres_url, kind="chat")
        session_id = str(session["id"])

    # Store user message
    await add_message(settings.postgres_url, session_id, "user", req.message)

    # Get RAG context
    rag_context = ""
    try:
        hits = await rag_module.query(req.message, limit=3)
        if hits:
            segments = [f"[{h['source']}]: {h['text']}" for h in hits]
            rag_context = "\n\n".join(segments)
    except Exception as e:
        logger.warning(f"RAG query failed: {e}")

    # Route through state machine with 1 iteration for simple chat
    client = _get_llm_client()
    sm = AgentStateMachine(
        session_id=session_id,
        task=req.message,
        model=model,
        llm_client=client,
        database_url=settings.postgres_url,
        max_iterations=1,
        rag_context=rag_context,
    )

    response_text = ""
    async for event_str in sm.run():
        # Parse SSE event to extract text content
        for line in event_str.split("\n"):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("type") == "text":
                        response_text = data.get("content", "")
                except json.JSONDecodeError:
                    pass

    if not response_text:
        # Fallback: direct LLM call
        from apps.agent_runtime.chat import handle_chat
        response_text = await handle_chat(
            client=client,
            message=req.message,
            model=model,
            context=req.context,
            history=req.history,
            images=req.images,
        )

    # Store assistant message
    await add_message(settings.postgres_url, session_id, "assistant", response_text)

    return {
        "session_id": session_id,
        "response": response_text,
        "model": model,
    }


@router.post("/code/stream")
async def agent_code_stream(req: AgentStreamRequest):
    """SSE streaming agent endpoint for coding tasks."""
    model = req.model or settings.default_model
    session_id = req.session_id

    if not session_id:
        session = await create_session(settings.postgres_url, kind="agentic")
        session_id = str(session["id"])

    await add_message(settings.postgres_url, session_id, "user", req.task)

    client = _get_llm_client()

    # Get RAG context
    rag_context = ""
    try:
        hits = await rag_module.query(req.task, limit=3)
        if hits:
            segments = [f"[{h['source']}]: {h['text']}" for h in hits]
            rag_context = "\n\n".join(segments)
    except Exception:
        pass

    sm = AgentStateMachine(
        session_id=session_id,
        task=req.task,
        model=model,
        llm_client=client,
        database_url=settings.postgres_url,
        max_iterations=req.max_iterations,
        rag_context=rag_context,
    )

    async def event_generator():
        async for event_str in sm.run():
            yield event_str
        # Final event
        yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class ApproveRequest(BaseModel):
    tool_call_id: str


class RejectRequest(BaseModel):
    tool_call_id: str
    feedback: str = "Rejected by user."


@router.post("/code/approve")
async def approve_tool(req: ApproveRequest):
    """Approve a pending tool call, unblocking the agent loop."""
    approved = await approve_tool_call(
        database_url=settings.postgres_url,
        tool_call_id=req.tool_call_id,
    )
    return {"status": "ok" if approved else "not_found"}


@router.post("/code/reject")
async def reject_tool(req: RejectRequest):
    """Reject a pending tool call with feedback, unblocking the agent loop."""
    rejected = await reject_tool_call(
        database_url=settings.postgres_url,
        tool_call_id=req.tool_call_id,
        feedback=req.feedback,
    )
    return {"status": "ok" if rejected else "not_found"}


WORKSPACE_ROOT = os.getenv("SPARK_WORKSPACE_ROOT", "/workspace")


@router.get("/code/memory")
async def get_memory():
    """Get agent memory file."""
    memory_path = os.path.join(WORKSPACE_ROOT, ".spark_coder", "MEMORY.md")
    if not os.path.exists(memory_path):
        return {"memory": ""}
    try:
        with open(memory_path, encoding="utf-8") as f:
            return {"memory": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read memory: {e}")


class MemoryRequest(BaseModel):
    memory: str


@router.post("/code/memory")
async def post_memory(req: MemoryRequest):
    """Update agent memory file."""
    memory_path = os.path.join(WORKSPACE_ROOT, ".spark_coder", "MEMORY.md")
    try:
        os.makedirs(os.path.dirname(memory_path), exist_ok=True)
        with open(memory_path, "w", encoding="utf-8") as f:
            f.write(req.memory)
        return {"status": "ok", "message": "Memory updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write memory: {e}")


@router.get("/code/replay/{session_id}")
async def replay_session(session_id: str):
    """Return full session history for debugging."""
    sessions_dir = os.path.join(WORKSPACE_ROOT, ".spark_coder", "sessions")
    path = os.path.join(sessions_dir, f"{session_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read session: {e}")


class MultiAgentRequest(BaseModel):
    task: str
    session_id: str | None = None
    model: str | None = None
    roles: str = "coder,reviewer,tester"


@router.post("/code/multi-agent")
async def multi_agent_stream(req: MultiAgentRequest):
    """Multi-agent coding loop with specialized roles (SSE)."""
    model = req.model or settings.default_model
    session_id = req.session_id or str(uuid.uuid4())

    await add_message(settings.postgres_url, session_id, "user", req.task)

    client = _get_llm_client()
    sm = AgentStateMachine(
        session_id=session_id,
        task=req.task,
        model=model,
        llm_client=client,
        database_url=settings.postgres_url,
        max_iterations=15,
    )

    async def event_generator():
        async for event_str in sm.run():
            yield event_str
        yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
