"""Publishing routes — metadata, upload, schedule."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.media_workers.publishing import (
    generate_metadata,
    get_schedule,
    schedule_video,
    upload_video,
)
from apps.media_workers.scheduler import get_scheduler

router = APIRouter(prefix="/api/publish", tags=["publish"])


class MetadataRequest(BaseModel):
    title: str
    description: str
    tags: list[str] = []


class UploadRequest(BaseModel):
    file_path: str
    metadata: dict = {}


class ScheduleRequest(BaseModel):
    title: str
    publish_time: str


@router.post("/metadata")
async def generate_metadata_endpoint(req: MetadataRequest):
    return await generate_metadata(req.title, req.description, req.tags)


@router.post("/upload")
async def upload_video_endpoint(req: UploadRequest):
    return await upload_video(req.file_path, req.metadata)


@router.get("/schedule")
async def get_schedule_endpoint():
    return await get_schedule()


@router.post("/schedule")
async def schedule_video_endpoint(req: ScheduleRequest):
    return await schedule_video(req.title, req.publish_time)


@router.get("/scheduler/queue")
async def scheduler_queue_endpoint():
    scheduler = get_scheduler()
    return await scheduler.list_pending()


@router.post("/scheduler/add")
async def scheduler_add_endpoint(req: ScheduleRequest):
    scheduler = get_scheduler()
    return await scheduler.add({
        "title": req.title,
        "scheduled_time": req.publish_time,
    })


@router.post("/scheduler/cancel/{job_id}")
async def scheduler_cancel_endpoint(job_id: str):
    scheduler = get_scheduler()
    cancelled = await scheduler.cancel(job_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Scheduled job not found or already dispatched")
    return {"job_id": job_id, "status": "cancelled"}
