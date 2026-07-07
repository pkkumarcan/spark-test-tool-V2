"""YouTube publishing — mock upload + metadata generation."""

import datetime
import logging
import os
import random
import uuid

logger = logging.getLogger("spark.media.publishing")

SCHEDULED_QUEUE: list[dict] = [
    {
        "publish_id": "pub-101",
        "title": "Spark AI Tutorial - Getting Started",
        "scheduled_time": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat(),
        "status": "scheduled",
        "platform": "youtube",
    },
    {
        "publish_id": "pub-102",
        "title": "Unlocking ComfyUI Consistency Secrets",
        "scheduled_time": (datetime.datetime.now() + datetime.timedelta(days=3)).isoformat(),
        "status": "scheduled",
        "platform": "youtube",
    },
]


async def generate_metadata(title: str, description: str, tags: list[str]) -> dict:
    return {
        "title": title[:100],
        "description": f"{description}\n\n[Sponsored / Disclosures]\nProduced automatically by Spark AI Factory.",
        "tags": tags[:30],
        "category_id": "27",
        "status": "draft",
        "generated_at": datetime.datetime.now().isoformat(),
    }


async def upload_video(file_path: str, metadata: dict) -> dict:
    if file_path and not os.path.exists(file_path):
        if not file_path.startswith("mock_"):
            logger.warning(f"Video file not found at: {file_path}")

    video_id = "".join(
        random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", k=11)
    )

    return {
        "status": "success",
        "platform": "youtube",
        "video_id": video_id,
        "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        "uploaded_at": datetime.datetime.now().isoformat(),
        "metadata": metadata,
    }


async def get_schedule() -> dict:
    return {"queue": SCHEDULED_QUEUE}


async def schedule_video(title: str, publish_time: str) -> dict:
    new_event = {
        "publish_id": f"pub-{uuid.uuid4().hex[:6]}",
        "title": title,
        "scheduled_time": publish_time,
        "status": "scheduled",
        "platform": "youtube",
    }
    SCHEDULED_QUEUE.append(new_event)
    return new_event
