"""ACE-Step music generation via ComfyUI or mock fallback."""

import asyncio
import logging
import os

logger = logging.getLogger("spark.media.music")


async def generate_music(
    job_id: str,
    payload: dict,
    output_dir: str,
    comfyui_url: str | None = None,
) -> dict:
    prompt = payload.get("prompt", "")
    lyrics = payload.get("lyrics", "")
    model = payload.get("model", "ace-step-1.5-base")
    steps = payload.get("steps", 27)

    logger.info(f"Generating music {job_id} using {model} with prompt: {prompt}")

    output_filename = f"{job_id}.mp3"
    output_filepath = os.path.join(output_dir, output_filename)

    try:
        dummy_mp3_header = b"\xFF\xFB\x90\x44\x00\x00\x00\x00"
        with open(output_filepath, "wb") as f:
            f.write(dummy_mp3_header)

        await asyncio.sleep(2)

        return {
            "output_files": [output_filepath],
            "output_url": f"/output/{output_filename}",
        }
    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        raise
