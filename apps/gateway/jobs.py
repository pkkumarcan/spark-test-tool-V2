"""Postgres-backed job store — replaces V1's SQLite + in-memory dict."""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import asyncpg
from procrastinate import App, PsycopgConnector

logger = logging.getLogger("spark.gateway.jobs")

_pool: asyncpg.Pool | None = None
_procrastinate_app: App | None = None

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"


async def init_pool(dsn: str) -> asyncpg.Pool:
    global _pool, _procrastinate_app
    _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
    connector = PsycopgConnector(conninfo=dsn)
    _procrastinate_app = App(connector=connector)
    await _procrastinate_app.open_async()
    return _pool


async def close_pool():
    global _pool, _procrastinate_app
    if _procrastinate_app:
        await _procrastinate_app.close_async()
        _procrastinate_app = None
    if _pool:
        await _pool.close()
        _pool = None


async def _get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Job pool not initialised — call init_pool() first")
    return _pool


async def create_job(
    kind: str,
    payload: dict,
    priority: int = 0,
    max_retries: int = 3,
) -> str:
    pool = await _get_pool()
    job_id = uuid4()
    await pool.execute(
        """
        INSERT INTO jobs (id, kind, status, priority, payload, max_retries, created_at)
        VALUES ($1, $2, $3, $4, $5::jsonb, $6, now())
        """,
        job_id,
        kind,
        STATUS_PENDING,
        priority,
        __import__("json").dumps(payload),
        max_retries,
    )
    logger.info(f"Job created: {job_id} (kind={kind})")

    # Defer Procrastinate task
    if _procrastinate_app:
        task_name = f"execute_{kind}_job"
        if kind == "video_test":
            task_name = "execute_video_job"

        valid_tasks = {
            "execute_image_job",
            "execute_video_job",
            "execute_music_job",
            "execute_tts_job",
            "execute_stt_job",
            "execute_meme_job",
            "execute_postprocess_job",
            "execute_extraction_job",
            "execute_3d_job",
        }

        if task_name in valid_tasks:
            queue_map = {
                "image": "image",
                "video": "video",
                "video_test": "video",
                "music": "music",
                "tts": "audio",
                "stt": "audio",
                "3d": "image",
                "meme": "image",
                "postprocess": "image",
                "extraction": "audio",
            }
            queue_name = queue_map.get(kind, "default")
            try:
                await _procrastinate_app.configure_task(name=task_name, queue=queue_name).defer_async(
                    job_id=str(job_id),
                    payload=payload,
                )
                logger.info(f"Deferred Procrastinate task '{task_name}' on queue '{queue_name}' for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to defer Procrastinate task '{task_name}' for job {job_id}: {e}")

    return str(job_id)


async def update_job(
    job_id: str,
    *,
    status: str | None = None,
    gpu_node: str | None = None,
    result: dict | None = None,
    error: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    retry_count: int | None = None,
):
    pool = await _get_pool()
    sets = []
    params: list[Any] = []
    idx = 1

    if status is not None:
        sets.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    if gpu_node is not None:
        sets.append(f"gpu_node = ${idx}")
        params.append(gpu_node)
        idx += 1
    if result is not None:
        import json
        sets.append(f"result = ${idx}::jsonb")
        params.append(json.dumps(result))
        idx += 1
    if error is not None:
        sets.append(f"error = ${idx}")
        params.append(error)
        idx += 1
    if started_at is not None:
        sets.append(f"started_at = ${idx}")
        params.append(started_at)
        idx += 1
    if finished_at is not None:
        sets.append(f"finished_at = ${idx}")
        params.append(finished_at)
        idx += 1
    if retry_count is not None:
        sets.append(f"retry_count = ${idx}")
        params.append(retry_count)
        idx += 1

    if not sets:
        return

    params.append(job_id)
    query = f"UPDATE jobs SET {', '.join(sets)} WHERE id = ${idx}"
    await pool.execute(query, *params)


async def get_job(job_id: str) -> dict | None:
    pool = await _get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM jobs WHERE id = $1",
        job_id,
    )
    if row is None:
        return None
    return dict(row)


async def list_jobs(
    status: str | None = None,
    kind: str | None = None,
    limit: int = 50,
) -> list[dict]:
    pool = await _get_pool()
    conditions = []
    params: list[Any] = []
    idx = 1

    if status is not None:
        conditions.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    if kind is not None:
        conditions.append(f"kind = ${idx}")
        params.append(kind)
        idx += 1

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    query = f"SELECT * FROM jobs{where} ORDER BY created_at DESC LIMIT ${idx}"
    rows = await pool.fetch(query, *params)
    return [dict(r) for r in rows]


async def cancel_job(job_id: str) -> bool:
    pool = await _get_pool()
    result = await pool.execute(
        """
        UPDATE jobs SET status = $1, finished_at = now()
        WHERE id = $2 AND status IN ($3, $4)
        """,
        STATUS_CANCELLED,
        job_id,
        STATUS_PENDING,
        STATUS_RUNNING,
    )
    return result.endswith("UPDATE 1")
