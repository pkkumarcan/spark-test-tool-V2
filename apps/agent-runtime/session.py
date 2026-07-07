"""Postgres-backed session persistence."""

from __future__ import annotations

import json
import logging
import uuid

import asyncpg

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def get_pool(database_url: str) -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def init_db(database_url: str) -> None:
    pool = await get_pool(database_url)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id TEXT NOT NULL DEFAULT 'default',
                kind TEXT NOT NULL DEFAULT 'chat',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                tool_calls JSONB DEFAULT '[]',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS tool_calls (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                tool_name TEXT NOT NULL,
                args JSONB NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                result JSONB,
                requires_approval BOOLEAN NOT NULL DEFAULT false,
                approved_at TIMESTAMPTZ,
                approved_by TEXT,
                sandbox_container_id TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)


async def create_session(
    database_url: str,
    kind: str = "chat",
    user_id: str = "default",
) -> dict:
    pool = await get_pool(database_url)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO sessions (user_id, kind) VALUES ($1, $2)
               RETURNING id, user_id, kind, status, created_at, updated_at""",
            user_id,
            kind,
        )
        return dict(row)


async def add_message(
    database_url: str,
    session_id: str,
    role: str,
    content: str,
    tool_calls: list[dict] | None = None,
) -> dict:
    pool = await get_pool(database_url)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO messages (session_id, role, content, tool_calls)
               VALUES ($1, $2, $3, $4)
               RETURNING id, session_id, role, content, tool_calls, created_at""",
            uuid.UUID(session_id),
            role,
            content,
            json.dumps(tool_calls or []),
        )
        return dict(row)


async def get_messages(
    database_url: str,
    session_id: str,
    limit: int = 50,
) -> list[dict]:
    pool = await get_pool(database_url)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, session_id, role, content, tool_calls, created_at
               FROM messages WHERE session_id = $1
               ORDER BY created_at ASC LIMIT $2""",
            uuid.UUID(session_id),
            limit,
        )
        return [dict(r) for r in rows]


async def update_session_status(
    database_url: str,
    session_id: str,
    status: str,
) -> None:
    pool = await get_pool(database_url)
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE sessions SET status = $1, updated_at = now() WHERE id = $2""",
            status,
            uuid.UUID(session_id),
        )


async def create_tool_call(
    database_url: str,
    message_id: str,
    tool_name: str,
    args: dict,
    requires_approval: bool = False,
) -> dict:
    pool = await get_pool(database_url)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO tool_calls (message_id, tool_name, args, requires_approval)
               VALUES ($1, $2, $3, $4)
               RETURNING id, message_id, tool_name, args, status, requires_approval, created_at""",
            uuid.UUID(message_id),
            tool_name,
            json.dumps(args),
            requires_approval,
        )
        return dict(row)


async def update_tool_call_status(
    database_url: str,
    tool_call_id: str,
    status: str,
    result: dict | None = None,
) -> None:
    pool = await get_pool(database_url)
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE tool_calls SET status = $1, result = $2 WHERE id = $3""",
            status,
            json.dumps(result) if result else None,
            uuid.UUID(tool_call_id),
        )
