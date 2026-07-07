# ADR-003: Procrastinate for Job Queue

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** Spark Engineering

## Context

V1 used SQLite + asyncio tasks for job management:
- `job_store.py` managed a SQLite database for job state
- Background tasks tracked via `asyncio.create_task()` in memory
- No VRAM-aware scheduling (flat `Semaphore(2)`)
- Job cancellation was fragile (in-memory task references)
- No retry logic for failed jobs

## Decision

Use Procrastinate, a Python library with a Postgres-backed job queue, for all media generation jobs.

## Consequences

**Positive:**
- Jobs persisted in Postgres — survive gateway restarts
- Built-in retry logic with configurable backoff
- Queue priorities and scheduling
- Worker management (separate media-workers service)
- VRAM-aware scheduling via gpu_nodes table + heartbeat
- No additional services (Redis, RabbitMQ) — Postgres handles both state and queue

**Negative:**
- Procrastinate is less mature than Celery/RQ
- Requires worker process management
- Learning curve for Procrastinate-specific patterns

**Mitigations:**
- Procrastinate is actively maintained and well-documented
- Docker Compose manages worker lifecycle
- Simple task definitions (decorator-based) are easy to understand

## Alternatives Considered

1. **Celery** — powerful but requires Redis/RabbitMQ broker, overkill for single-machine setup
2. **RQ (Redis Queue)** — requires Redis, simpler but less featured
3. **asyncio tasks** — V1 approach, no persistence, no retry
4. **Temporal** — powerful workflow engine, too complex for this use case
5. **Ray** — distributed computing framework, overkill
