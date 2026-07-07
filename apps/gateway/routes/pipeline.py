"""Pipeline CRUD + approval + status routes."""


from datetime import UTC

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.agent_runtime.pipeline import (
    PipelineRunner,
    create_pipeline,
    get_pipeline,
    list_pipelines,
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineCreateRequest(BaseModel):
    channel_id: str
    topic: str


class PipelineApprovalRequest(BaseModel):
    approved: bool
    feedback: str = ""


@router.post("/create")
async def create_pipeline_endpoint(req: PipelineCreateRequest):
    state = create_pipeline(req.channel_id, req.topic)
    return state.to_dict()


@router.get("/list")
async def list_pipelines_endpoint():
    return list_pipelines()


@router.get("/{pipeline_id}")
async def get_pipeline_endpoint(pipeline_id: str):
    state = get_pipeline(pipeline_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return state.to_dict()


@router.post("/{pipeline_id}/approve")
async def approve_pipeline_endpoint(pipeline_id: str, req: PipelineApprovalRequest):
    state = get_pipeline(pipeline_id)
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
    state = get_pipeline(pipeline_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    import asyncio
    runner = PipelineRunner(state)
    asyncio.create_task(runner.run_full())

    return {"pipeline_id": pipeline_id, "status": "started"}


@router.post("/{pipeline_id}/run-stage/{stage}")
async def run_pipeline_stage_endpoint(pipeline_id: str, stage: str):
    state = get_pipeline(pipeline_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    from apps.agent_runtime.pipeline import PipelineStage
    try:
        target_stage = PipelineStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    import asyncio
    runner = PipelineRunner(state)
    asyncio.create_task(runner.run_stage(target_stage))

    return {"pipeline_id": pipeline_id, "stage": stage, "status": "started"}
