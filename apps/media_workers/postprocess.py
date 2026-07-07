"""Post-processing — upscale + lipsync."""

import asyncio
import logging
import os
import shutil

logger = logging.getLogger("spark.media.postprocess")


async def upscale_image(
    job_id: str,
    payload: dict,
    output_dir: str,
) -> dict:
    image_url = payload.get("image_url", "")
    scale = payload.get("scale", 4)

    if not image_url:
        raise ValueError("Image URL is required")

    local_filename = image_url.replace("/output/", "")
    local_filepath = os.path.join(output_dir, local_filename)
    output_filename = f"{job_id}.png"
    output_filepath = os.path.join(output_dir, output_filename)

    if os.path.exists(local_filepath):
        shutil.copy(local_filepath, output_filepath)
    else:
        with open(output_filepath, "wb") as f:
            f.write(b"\x89PNG dummy upscaled placeholder")

    await asyncio.sleep(1.5)

    return {
        "output_files": [output_filepath],
        "output_url": f"/output/{output_filename}",
    }


async def lipsync_video(
    job_id: str,
    payload: dict,
    output_dir: str,
) -> dict:
    video_url = payload.get("video_url", "")
    audio_url = payload.get("audio_url", "")

    if not video_url or not audio_url:
        raise ValueError("Video and Audio URLs are required")

    output_filename = f"{job_id}.mp4"
    output_filepath = os.path.join(output_dir, output_filename)

    local_video_filename = video_url.replace("/output/", "")
    local_video_filepath = os.path.join(output_dir, local_video_filename)

    if os.path.exists(local_video_filepath):
        shutil.copy(local_video_filepath, output_filepath)
    else:
        with open(output_filepath, "wb") as f:
            f.write(b"dummy synced video")

    await asyncio.sleep(2.0)

    return {
        "output_files": [output_filepath],
        "output_url": f"/output/{output_filename}",
    }
