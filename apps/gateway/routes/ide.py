"""IDE routes — /api/ide/* file system services for the coding agent."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ide", tags=["ide"])

WORKSPACE_ROOT = os.getenv("SPARK_WORKSPACE_ROOT", "/workspace")


def _is_safe_path(path: str) -> bool:
    abs_path = os.path.realpath(os.path.join(WORKSPACE_ROOT, path))
    return abs_path.startswith(os.path.realpath(WORKSPACE_ROOT))


@router.get("/files")
async def list_files():
    """Recursively list files and directories inside the workspace."""

    def build_tree(current_dir: str) -> list:
        items = []
        skip = {".git", ".spark_coder", "node_modules", "__pycache__", "cache", ".env", "qdrant_storage"}
        try:
            for entry in os.scandir(current_dir):
                if entry.name in skip or entry.name.startswith("."):
                    continue
                rel_path = os.path.relpath(entry.path, WORKSPACE_ROOT)
                if entry.is_dir():
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": "directory",
                        "children": build_tree(entry.path),
                    })
                else:
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": "file",
                    })
        except PermissionError:
            pass
        items.sort(key=lambda x: (0 if x.get("type") == "directory" else 1, str(x.get("name", "")).lower()))
        return items

    try:
        tree = build_tree(WORKSPACE_ROOT)
        return {"status": "ok", "files": tree, "workspace_root": WORKSPACE_ROOT}
    except Exception as e:
        logger.error(f"Failed to list workspace files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file")
async def read_file(path: str):
    """Read the content of a file."""
    if not path:
        raise HTTPException(status_code=400, detail="Path parameter is required")
    if not _is_safe_path(path):
        raise HTTPException(status_code=403, detail="Access denied. Path lies outside sandbox.")

    abs_path = os.path.realpath(os.path.join(WORKSPACE_ROOT, path))
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.isdir(abs_path):
        raise HTTPException(status_code=400, detail="Target path is a directory, not a file")

    try:
        with open(abs_path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        ext = os.path.splitext(path)[1].lower()
        lang_map = {
            ".py": "python", ".js": "javascript", ".html": "html", ".css": "css",
            ".json": "json", ".sh": "shell", ".md": "markdown", ".sql": "sql",
            ".yml": "yaml", ".yaml": "yaml", ".txt": "plaintext", ".ts": "typescript",
            ".tsx": "typescriptreact",
        }
        language = lang_map.get(ext, "plaintext")
        return {"status": "ok", "path": path, "content": content, "language": language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")


class WriteFileRequest(BaseModel):
    path: str
    content: str


@router.post("/file")
async def write_file(req: WriteFileRequest):
    """Write contents to a file."""
    path = req.path.strip()
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    if not _is_safe_path(path):
        raise HTTPException(status_code=403, detail="Access denied. Path lies outside sandbox.")

    abs_path = os.path.realpath(os.path.join(WORKSPACE_ROOT, path))
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "ok", "message": f"Written {len(req.content)} bytes to {path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")


class SetWorkspaceRequest(BaseModel):
    path: str


@router.post("/workspace")
async def set_workspace(req: SetWorkspaceRequest):
    """Change the workspace root directory."""
    path = req.path.strip()
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    if not os.path.exists(path) or not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Directory does not exist")

    global WORKSPACE_ROOT
    WORKSPACE_ROOT = path
    logger.info(f"Workspace root updated to: {path}")
    return {"status": "ok", "workspace_root": path}


@router.get("/workspace")
async def get_workspace():
    """Get the current workspace root directory."""
    return {"workspace_root": WORKSPACE_ROOT}


@router.get("/stream")
async def ide_stream(task: str, session_id: str | None = None, model: str | None = None, max_iterations: int = 15):
    """GET stream endpoint for the frontend IDE page."""
    import json
    from fastapi.responses import StreamingResponse
    from apps.gateway.config import settings
    from apps.agent_runtime.session import create_session, add_message
    from apps.agent_runtime.state_machine import AgentStateMachine
    from apps.gateway.routes.agent import _get_llm_client, rag_module

    model = model or settings.default_model

    if not session_id:
        session = await create_session(settings.postgres_url, kind="agentic")
        session_id = str(session["id"])

    await add_message(settings.postgres_url, session_id, "user", task)

    client = _get_llm_client()

    # Get RAG context
    rag_context = ""
    try:
        hits = await rag_module.query(task, limit=3)
        if hits:
            segments = [f"[{h['source']}]: {h['text']}" for h in hits]
            rag_context = "\n\n".join(segments)
    except Exception:
        pass

    sm = AgentStateMachine(
        session_id=session_id,
        task=task,
        model=model,
        llm_client=client,
        database_url=settings.postgres_url,
        max_iterations=max_iterations,
        rag_context=rag_context,
    )

    async def event_generator():
        async for event_str in sm.run():
            yield event_str
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
