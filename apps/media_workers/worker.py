"""Procrastinate worker entry point — Postgres-backed queue for all media jobs."""

import asyncio
import logging
import os
from datetime import UTC, datetime

import procrastinate
from procrastinate import App, PsycopgConnector, RetryStrategy

class VRAMRetryError(Exception):
    """Exception raised when there is not enough VRAM to run a job."""
    pass

vram_retry_strategy = RetryStrategy(
    max_attempts=99,
    wait=30,
    retry_exceptions={VRAMRetryError}
)

from apps.media_workers.three_d import generate_3d
from apps.media_workers.comfyui_client import ComfyUIClient
from apps.media_workers.extraction import extract_link, extract_youtube, ocr_image
from apps.media_workers.image import generate_image
from apps.media_workers.music import generate_music
from apps.media_workers.postprocess import lipsync_video, upscale_image
from apps.media_workers.stt import transcribe_audio
from apps.media_workers.tts import synthesize_speech
from apps.media_workers.video import generate_video
from apps.media_workers.vram_tracker import (
    get_available_node,
    heartbeat_loop,
    release_vram,
    reserve_vram,
)

logger = logging.getLogger("spark.media.worker")

pg_host = os.getenv("SPARK_POSTGRES_HOST", "postgres")
pg_port = os.getenv("SPARK_POSTGRES_PORT", "5432")
pg_user = os.getenv("SPARK_POSTGRES_USER", "spark")
pg_pass = os.getenv("SPARK_POSTGRES_PASSWORD", "spark")
pg_db = os.getenv("SPARK_POSTGRES_DB", "spark")
connector = PsycopgConnector(conninfo=f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}")
app = App(connector=connector)

comfyui_client = ComfyUIClient(
    comfyui_url=os.getenv("SPARK_COMFYUI_URL", "http://host.docker.internal:8188"),
    output_dir=os.getenv("OUTPUT_DIR", "/comfyui-output"),
)

NODE_NAME = os.getenv("GPU_NODE_NAME", "gpu-node-1")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")
OLLAMA_URL = os.getenv("SPARK_OLLAMA_BASE_URL", "http://localhost:11434")
F5_TTS_URL = os.getenv("F5_TTS_URL", "http://f5-tts:8000")
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:9000")

VRAM_REQUIREMENTS = {
    "image": 4096,
    "video": 8192,
    "music": 4096,
    "tts": 2048,
    "3d": 6144,
}


async def _get_pool():
    import asyncpg
    return await asyncpg.create_pool(
        host=os.getenv("SPARK_POSTGRES_HOST", "postgres"),
        port=int(os.getenv("SPARK_POSTGRES_PORT", "5432")),
        user=os.getenv("SPARK_POSTGRES_USER", "spark"),
        password=os.getenv("SPARK_POSTGRES_PASSWORD", "spark"),
        database=os.getenv("SPARK_POSTGRES_DB", "spark"),
    )


async def _run_with_vram(job_id: str, kind: str, handler):

    from apps.gateway.jobs import update_job

    pool = await _get_pool()
    vram_needed = VRAM_REQUIREMENTS.get(kind, 4096)

    try:
        node = await get_available_node(pool, vram_needed)
        if not node:
            logger.info(f"No VRAM for {kind} job {job_id}, retrying in 30s")
            raise VRAMRetryError(f"No VRAM available for {kind} job")

        node_name = node["name"]
        await update_job(job_id, status="running", gpu_node=node_name)
        await reserve_vram(pool, node_name, vram_needed)

        try:
            result = await handler()
            await update_job(
                job_id,
                status="completed",
                result=result,
                finished_at=datetime.now(UTC),
            )
            logger.info(f"{kind} job {job_id} completed")
        except VRAMRetryError:
            # Propagate VRAMRetryError without setting to failed
            raise
        except Exception as e:
            logger.error(f"{kind} job {job_id} failed: {e}")
            await update_job(
                job_id,
                status="failed",
                error=str(e),
                finished_at=datetime.now(UTC),
            )
            raise
        finally:
            await release_vram(pool, node_name, vram_needed)
    except VRAMRetryError:
        # Reset status to pending so it can be retried
        await update_job(job_id, status="pending")
        raise
    finally:
        await pool.close()


@app.task(queue="image", name="execute_image_job", retry=vram_retry_strategy)
async def execute_image_job(job_id: str, payload: dict):
    await _run_with_vram(job_id, "image", lambda: generate_image(comfyui_client, job_id, payload))


@app.task(queue="image", name="execute_3d_job", retry=vram_retry_strategy)
async def execute_3d_job(job_id: str, payload: dict):
    await _run_with_vram(job_id, "3d", lambda: generate_3d(comfyui_client, job_id, payload))


@app.task(queue="video", name="execute_video_job", retry=vram_retry_strategy)
async def execute_video_job(job_id: str, payload: dict):
    await _run_with_vram(job_id, "video", lambda: generate_video(comfyui_client, job_id, payload))


@app.task(queue="music", name="execute_music_job")
async def execute_music_job(job_id: str, payload: dict):
    from apps.gateway.jobs import update_job
    await update_job(job_id, status="running")
    try:
        result = await generate_music(job_id, payload, OUTPUT_DIR, comfyui_url=os.getenv("SPARK_COMFYUI_URL"))
        await update_job(job_id, status="completed", result=result, finished_at=datetime.now(UTC))
    except Exception as e:
        await update_job(job_id, status="failed", error=str(e), finished_at=datetime.now(UTC))
        raise


@app.task(queue="audio", name="execute_tts_job")
async def execute_tts_job(job_id: str, payload: dict):
    from apps.gateway.jobs import update_job
    await update_job(job_id, status="running")
    try:
        result = await synthesize_speech(job_id, payload, OUTPUT_DIR, f5_tts_url=F5_TTS_URL)
        await update_job(job_id, status="completed", result=result, finished_at=datetime.now(UTC))
    except Exception as e:
        await update_job(job_id, status="failed", error=str(e), finished_at=datetime.now(UTC))
        raise


@app.task(queue="audio", name="execute_stt_job")
async def execute_stt_job(job_id: str, payload: dict):
    from apps.gateway.jobs import update_job
    await update_job(job_id, status="running")
    try:
        result = await transcribe_audio(job_id, payload, OUTPUT_DIR, whisper_url=WHISPER_URL)
        await update_job(job_id, status="completed", result=result, finished_at=datetime.now(UTC))
    except Exception as e:
        await update_job(job_id, status="failed", error=str(e), finished_at=datetime.now(UTC))
        raise


@app.task(queue="image", name="execute_meme_job", retry=vram_retry_strategy)
async def execute_meme_job(job_id: str, payload: dict):
    from apps.media_workers.meme import generate_meme
    await _run_with_vram(job_id, "image", lambda: generate_meme(comfyui_client, job_id, payload, OUTPUT_DIR, ollama_url=OLLAMA_URL))


@app.task(queue="image", name="execute_postprocess_job")
async def execute_postprocess_job(job_id: str, payload: dict):
    from apps.gateway.jobs import update_job
    action = payload.get("action", "upscale")
    await update_job(job_id, status="running")
    try:
        if action == "upscale":
            result = await upscale_image(job_id, payload, OUTPUT_DIR)
        elif action == "lipsync":
            result = await lipsync_video(job_id, payload, OUTPUT_DIR)
        else:
            raise ValueError(f"Unknown postprocess action: {action}")
        await update_job(job_id, status="completed", result=result, finished_at=datetime.now(UTC))
    except Exception as e:
        await update_job(job_id, status="failed", error=str(e), finished_at=datetime.now(UTC))
        raise


@app.task(queue="audio", name="execute_extraction_job")
async def execute_extraction_job(job_id: str, payload: dict):
    from apps.gateway.jobs import update_job
    action = payload.get("action", "link")
    await update_job(job_id, status="running")
    try:
        if action == "ocr":
            result = await ocr_image(job_id, payload, OUTPUT_DIR, ollama_url=OLLAMA_URL)
        elif action == "link":
            result = await extract_link(job_id, payload.get("url", ""), OUTPUT_DIR)
        elif action == "youtube":
            result = await extract_youtube(job_id, payload.get("url", ""), OUTPUT_DIR)
        else:
            raise ValueError(f"Unknown extraction action: {action}")
        await update_job(job_id, status="completed", result=result, finished_at=datetime.now(UTC))
    except Exception as e:
        await update_job(job_id, status="failed", error=str(e), finished_at=datetime.now(UTC))
        raise


JOB_QUEUE_MAP = {
    "image": ["image"],
    "video": ["video"],
    "music": ["music"],
    "tts": ["audio"],
    "stt": ["audio"],
    "3d": ["image"],
    "meme": ["image"],
    "postprocess": ["image"],
    "extraction": ["audio"],
}


async def run_worker(queues: list[str] | None = None):
    from apps.gateway.jobs import init_pool, close_pool

    pg_host = os.getenv("SPARK_POSTGRES_HOST", "postgres")
    pg_port = os.getenv("SPARK_POSTGRES_PORT", "5432")
    pg_user = os.getenv("SPARK_POSTGRES_USER", "spark")
    pg_pass = os.getenv("SPARK_POSTGRES_PASSWORD", "spark")
    pg_db = os.getenv("SPARK_POSTGRES_DB", "spark")
    dsn = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    await init_pool(dsn)

    pool = await _get_pool()
    heartbeat_task = asyncio.create_task(heartbeat_loop(pool, NODE_NAME))

    listen_queues = queues or ["image", "video", "audio", "music"]
    logger.info(f"Starting Procrastinate worker (node={NODE_NAME}, queues={listen_queues})")
    try:
        async with app.open_async():
            await app.run_worker_async(queues=listen_queues, wait=True)
    finally:
        heartbeat_task.cancel()
        await pool.close()
        await close_pool()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
