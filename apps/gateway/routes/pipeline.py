"""Pipeline CRUD + approval + status routes."""


import os
from datetime import UTC
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from apps.agent_runtime.pipeline import (
    PipelineRunner,
    async_create_pipeline,
    async_get_pipeline,
    async_list_pipelines,
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

OUTPUT_DIR = os.getenv("SPARK_OUTPUT_DIR", "/app/output")


class PipelineCreateRequest(BaseModel):
    channel_id: str
    topic: str


class PipelineApprovalRequest(BaseModel):
    approved: bool
    feedback: str = ""


@router.post("/create")
async def create_pipeline_endpoint(req: PipelineCreateRequest):
    state = await async_create_pipeline(req.channel_id, req.topic)
    return state.to_dict()


@router.get("/list")
async def list_pipelines_endpoint():
    return await async_list_pipelines()


@router.get("/{pipeline_id}")
async def get_pipeline_endpoint(pipeline_id: str):
    state = await async_get_pipeline(pipeline_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return state.to_dict()


@router.post("/{pipeline_id}/approve")
async def approve_pipeline_endpoint(pipeline_id: str, req: PipelineApprovalRequest):
    state = await async_get_pipeline(pipeline_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    from datetime import datetime
    state.data["approval"] = {
        "status": "approved" if req.approved else "rejected",
        "feedback": req.feedback,
        "approved_at": datetime.now(UTC).isoformat(),
    }
    from apps.agent_runtime.pipeline import PipelineStage
    state.set_stage(
        PipelineStage.APPROVAL,
        "passed" if req.approved else "failed",
        100,
        "Approved" if req.approved else f"Rejected: {req.feedback}",
    )
    return state.to_dict()


@router.post("/{pipeline_id}/run")
async def run_pipeline_endpoint(pipeline_id: str):
    state = await async_get_pipeline(pipeline_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    import asyncio
    from apps.agent_runtime.pipeline import _database_url
    runner = PipelineRunner(state, database_url=_database_url)
    asyncio.create_task(runner.run_full())

    return {"pipeline_id": pipeline_id, "status": "started"}


@router.post("/{pipeline_id}/run-stage/{stage}")
async def run_pipeline_stage_endpoint(pipeline_id: str, stage: str):
    state = await async_get_pipeline(pipeline_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    from apps.agent_runtime.pipeline import PipelineStage
    try:
        target_stage = PipelineStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    import asyncio
    from apps.agent_runtime.pipeline import _database_url
    runner = PipelineRunner(state, database_url=_database_url)
    asyncio.create_task(runner.run_stage(target_stage))

    return {"pipeline_id": pipeline_id, "stage": stage, "status": "started"}


@router.get("/{pipeline_id}/output/{file_path:path}")
async def serve_pipeline_output(pipeline_id: str, file_path: str):
    job_dir = os.path.join(OUTPUT_DIR, "jobs", pipeline_id)
    full_path = os.path.normpath(os.path.join(job_dir, file_path))

    if not full_path.startswith(job_dir):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_types = {
        ".mp4": "video/mp4",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".json": "application/json",
        ".txt": "text/plain",
    }
    suffix = Path(full_path).suffix.lower()
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(full_path, media_type=media_type)


@router.get("/{pipeline_id}/files")
async def list_pipeline_files(pipeline_id: str):
    job_dir = os.path.join(OUTPUT_DIR, "jobs", pipeline_id)
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="Pipeline output not found")

    files = []
    for root, dirs, filenames in os.walk(job_dir):
        for fn in filenames:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, job_dir)
            files.append({
                "path": rel,
                "size": os.path.getsize(full),
                "url": f"/api/pipeline/{pipeline_id}/output/{rel}",
            })
    return {"files": files}
