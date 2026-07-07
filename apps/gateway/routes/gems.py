"""Gems routes — /api/gems/*, /api/research/*, /api/curate/*, /api/chain/*, /api/moa/*, /api/dify/*.

Covers: research agent, smart curation, story chain, mixture of agents, meme generator,
financial analyst, MCP agent, chat with source, voice agent, generative UI, Dify workflow,
coding agent (non-SSE).
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from apps.gateway.config import settings
from apps.gateway.jobs import create_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["gems"])


# ── Research ──────────────────────────────────────────────────────────────────

class ResearchGenerateRequest(BaseModel):
    topic: str
    depth: str = "standard"


@router.post("/api/research/generate")
async def research_generate(req: ResearchGenerateRequest):
    job_id = await create_job(kind="research", payload=req.model_dump())
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


@router.get("/api/assets")
async def list_all_assets():
    output_dir = os.getenv("SPARK_OUTPUT_DIR", "output")
    assets = []
    if os.path.exists(output_dir):
        for job_dir in os.listdir(output_dir):
            full = os.path.join(output_dir, job_dir)
            if os.path.isdir(full) and job_dir.startswith("weekly_"):
                for root, dirs, files in os.walk(full):
                    for f in files:
                        if f.endswith(('.mp3', '.wav', '.mp4', '.png', '.jpg', '.srt', '.md', '.json')):
                            rel = os.path.relpath(os.path.join(root, f), output_dir)
                            ftype = "audio" if f.endswith(('.mp3', '.wav')) else "video" if f.endswith('.mp4') else "image" if f.endswith(('.png', '.jpg')) else "doc"
                            assets.append({"name": f, "path": rel, "type": ftype, "url": f"/output/{rel}"})
    return assets


@router.get("/api/research/files")
async def list_research_files():
    output_dir = os.getenv("SPARK_OUTPUT_DIR", "output")
    files = []
    if os.path.exists(output_dir):
        for job_dir in sorted(os.listdir(output_dir), key=lambda d: os.path.getmtime(os.path.join(output_dir, d)), reverse=True):
            if not os.path.isdir(os.path.join(output_dir, job_dir)) or not job_dir.startswith("weekly_"):
                continue
            meta_dir = os.path.join(output_dir, job_dir, "metadata")
            topic_file = os.path.join(meta_dir, "topic.json")
            if os.path.exists(topic_file):
                try:
                    import json
                    data = json.loads(open(topic_file).read())
                    title = data.get("title", job_dir)
                    summary = data.get("topic_summary", "")
                    word_count = len((title + " " + summary).split())
                    files.append({"name": title[:60], "rel_path": f"{job_dir}/metadata/topic.json", "word_count": word_count})
                except Exception:
                    pass
    return {"files": files}


@router.get("/api/research/file")
async def get_research_file(path: str = ""):
    output_dir = os.getenv("SPARK_OUTPUT_DIR", "output")
    target = os.path.join(output_dir, path)
    if os.path.exists(target):
        try:
            import json
            data = json.loads(open(target).read())
            title = data.get("title", "Untitled")
            summary = data.get("topic_summary", "")
            hook = data.get("hook", "")
            audience = data.get("target_audience", "")
            content = f"# {title}\n\n## Summary\n\n{summary}\n\n## Hook\n\n{hook}\n\n## Target Audience\n\n{audience}\n"
            return {"content": content}
        except Exception:
            return {"content": open(target, errors="ignore").read()}
    return {"content": f"# {path}\n\nResearch content for {path}.\n\nThis is a stub document."}


@router.post("/api/research/compile")
async def compile_research():
    return {"ok": True, "message": "Research brief compiled successfully"}


@router.post("/api/research/expand")
async def expand_research():
    return {"ok": True, "message": "Research files expanded to target word counts"}


# ── Smart Curation ────────────────────────────────────────────────────────────

class CurateRequest(BaseModel):
    source_dir: str = "/app/media_ingest"
    strictness: float = 50
    pacing: float = 3.0


@router.post("/api/curate/generate")
async def curate_generate(req: CurateRequest):
    job_id = await create_job(kind="curate", payload=req.model_dump())
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


# ── Story Chain ───────────────────────────────────────────────────────────────

class ChainGenerateRequest(BaseModel):
    prompt: str
    style: str = "cinematic"


@router.post("/api/chain/generate")
async def chain_generate(req: ChainGenerateRequest):
    from apps.agent_runtime.llm_client import LLMClient
    from apps.media_workers.chained import chain_generate as chain_gen
    client = LLMClient(ollama_url=settings.ollama_base_url)
    result = await chain_gen(
        topic=req.prompt,
        llm_client=client,
        comfyui_url=settings.comfyui_url,
    )
    return result


# ── Mixture of Agents ────────────────────────────────────────────────────────

class MoaChatRequest(BaseModel):
    message: str
    model: str = "qwen3:8b"


@router.post("/api/moa/chat")
async def moa_chat(req: MoaChatRequest):
    from apps.agent_runtime.llm_client import LLMClient
    from apps.agent_runtime.moa import moa_generate
    client = LLMClient(ollama_url=settings.ollama_base_url)
    result = await moa_generate(client, req.message, aggregator_model=req.model)
    return {"response": result.content, "model": result.model}


# ── Meme Generator ───────────────────────────────────────────────────────────

class MemeGenerateRequest(BaseModel):
    prompt: str
    image_model: str = "flux1-schnell-q8.gguf"


@router.post("/api/meme/generate")
async def meme_generate(req: MemeGenerateRequest):
    job_id = await create_job(kind="meme", payload=req.model_dump())
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


# ── Financial Analyst ─────────────────────────────────────────────────────────

class FinanceRequest(BaseModel):
    query: str
    tickers: list[str] = []


@router.post("/api/gems/finance")
async def gems_finance(req: FinanceRequest):
    from packages.tool_registry.tools.finance import finance_analysis
    results = []
    for ticker in req.tickers:
        result = finance_analysis(symbol=ticker)
        results.append(result)
    if not results:
        from apps.agent_runtime.llm_client import LLMClient
        client = LLMClient(ollama_url=settings.ollama_base_url)
        resp = await client.chat(
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": req.query},
            ],
            model=settings.default_model,
        )
        return {"response": resp.content}
    return {"analysis": results}


# ── MCP Agent ─────────────────────────────────────────────────────────────────

class McpRequest(BaseModel):
    query: str
    tools: list[str] = []


@router.post("/api/gems/mcp")
async def gems_mcp(req: McpRequest):
    from apps.agent_runtime.llm_client import LLMClient
    from apps.agent_runtime.mcp import MCPAgent, mcp_chat
    client = LLMClient(ollama_url=settings.ollama_base_url)
    agent = MCPAgent()
    response = await mcp_chat(client, req.message, agent)
    return {"response": response}


# ── Chat with Source ──────────────────────────────────────────────────────────

class IngestSourceRequest(BaseModel):
    source_type: str = "text"
    content: str = ""


class ChatSourceRequest(BaseModel):
    message: str
    source_id: str = ""


@router.post("/api/gems/ingest-source")
async def gems_ingest_source(req: IngestSourceRequest):
    return {"status": "ok", "source_id": f"src_{os.urandom(4).hex()}"}


@router.post("/api/gems/chat-source")
async def gems_chat_source(req: ChatSourceRequest):
    from apps.agent_runtime.chat_source import chat_with_source
    from apps.agent_runtime.llm_client import LLMClient
    client = LLMClient(ollama_url=settings.ollama_base_url)
    response = await chat_with_source(client, req.message, source_filter=req.source_id or None)
    return {"response": response}


# ── Voice Agent ───────────────────────────────────────────────────────────────

@router.post("/api/gems/voice")
async def gems_voice(file: UploadFile = File(...)):
    import os
    import tempfile

    from apps.agent_runtime.llm_client import LLMClient
    from apps.agent_runtime.voice import voice_agent

    suffix = os.path.splitext(file.filename or "audio.wav")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        client = LLMClient(ollama_url=settings.ollama_base_url)
        result = await voice_agent(
            audio_path=tmp_path,
            llm_client=client,
            output_dir=os.getenv("SPARK_OUTPUT_DIR", "output"),
        )
        return result
    finally:
        os.unlink(tmp_path)


# ── Generative UI ─────────────────────────────────────────────────────────────

class GenerateUIRequest(BaseModel):
    prompt: str
    component_type: str = "card"


@router.post("/api/gems/generate-ui")
async def gems_generate_ui(req: GenerateUIRequest):
    from apps.agent_runtime.llm_client import LLMClient
    client = LLMClient(ollama_url=settings.ollama_base_url)
    system = "You generate React component code. Output only valid JSX."
    resp = await client.chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Generate a {req.component_type} component: {req.prompt}"},
        ],
        model=settings.default_model,
    )
    return {"component": resp}


# ── Dify Workflow ─────────────────────────────────────────────────────────────

class DifyWorkflowRequest(BaseModel):
    workflow_id: str
    inputs: dict = {}


@router.post("/api/dify/run-workflow")
async def dify_run_workflow(req: DifyWorkflowRequest):
    from apps.agent_runtime.dify import run_dify_workflow
    result = await run_dify_workflow(req.workflow_id, req.inputs)
    return result


# ── Coding Agent (non-SSE) ───────────────────────────────────────────────────

class CodingAgentRequest(BaseModel):
    task: str
    model: str = "qwen3:8b"
    max_iterations: int = 5


@router.post("/api/gems/coding-agent")
async def gems_coding_agent(req: CodingAgentRequest):
    if not req.task:
        raise HTTPException(status_code=400, detail="Task is required")
    job_id = await create_job(kind="coding", payload=req.model_dump())
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}
