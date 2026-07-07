"""Postgres-backed human-in-the-loop approval via LISTEN/NOTIFY."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

import asyncpg

logger = logging.getLogger(__name__)

_APPROVAL_CHANNEL = "tool_call_approval"


async def request_approval(
    database_url: str,
    tool_call_id: str,
    session_id: str,
    tool_name: str,
    tool_args: dict,
    diff: str = "",
    content: str = "",
    command: str = "",
) -> None:
    """Persist an approval request to Postgres and notify the gateway.

    The tool_calls row is updated to status='awaiting_approval', and a
    NOTIFY is sent so any listening gateway can push the approval card to
    the frontend immediately.
    """
    pool = await _get_pool(database_url)
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE tool_calls
               SET status = 'awaiting_approval'
               WHERE id = $1""",
            uuid.UUID(tool_call_id),
        )
        payload = json.dumps({
            "tool_call_id": tool_call_id,
            "session_id": session_id,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "diff": diff,
            "content": content,
            "command": command,
        })
        await conn.execute(
            f"SELECT pg_notify('{_APPROVAL_CHANNEL}', $1)",
            payload,
        )
    logger.info(f"Approval requested for tool_call {tool_call_id} ({tool_name})")


async def wait_for_decision(
    database_url: str,
    tool_call_id: str,
    timeout: float = 600.0,
) -> bool:
    """Block until the tool_call row is approved or rejected.

    Uses periodic database polling to prevent connection pool starvation.
    """
    pool = await _get_pool(database_url)
    start_time = asyncio.get_event_loop().time()
    approved = False

    while True:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT status, approved_at FROM tool_calls WHERE id = $1""",
                uuid.UUID(tool_call_id),
            )
            if row and row["status"] not in ("awaiting_approval", "pending"):
                approved = row["status"] == "completed" and row["approved_at"] is not None
                return approved

        if asyncio.get_event_loop().time() - start_time >= timeout:
            break

        await asyncio.sleep(1.0)

    return approved


async def approve_tool_call(
    database_url: str,
    tool_call_id: str,
    approved_by: str = "user",
) -> bool:
    """Mark a tool_call as approved and NOTIFY waiting agents."""
    pool = await _get_pool(database_url)
    async with pool.acquire() as conn:
        result = await conn.execute(
            """UPDATE tool_calls
               SET status = 'completed',
                   approved_at = now(),
                   approved_by = $2
               WHERE id = $1 AND status = 'awaiting_approval'""",
            uuid.UUID(tool_call_id),
            approved_by,
        )
        updated = result.endswith("1")
        if updated:
            payload = json.dumps({
                "tool_call_id": tool_call_id,
                "approved": True,
            })
            await conn.execute(
                f"SELECT pg_notify('{_APPROVAL_CHANNEL}', $1)",
                payload,
            )
        return updated


async def reject_tool_call(
    database_url: str,
    tool_call_id: str,
    feedback: str = "Rejected by user.",
    approved_by: str = "user",
) -> bool:
    """Mark a tool_call as rejected and NOTIFY waiting agents."""
    pool = await _get_pool(database_url)
    async with pool.acquire() as conn:
        result = await conn.execute(
            """UPDATE tool_calls
               SET status = 'failed',
                   approved_at = now(),
                   approved_by = $2,
                   result = jsonb_build_object('rejected', true, 'feedback', $3)
               WHERE id = $1 AND status = 'awaiting_approval'""",
            uuid.UUID(tool_call_id),
            approved_by,
            feedback,
        )
        updated = result.endswith("1")
        if updated:
            payload = json.dumps({
                "tool_call_id": tool_call_id,
                "approved": False,
                "feedback": feedback,
            })
            await conn.execute(
                f"SELECT pg_notify('{_APPROVAL_CHANNEL}', $1)",
                payload,
            )
        return updated


_pool: asyncpg.Pool | None = None


async def _get_pool(database_url: str) -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(database_url, min_size=2, max_size=5)
    return _pool
