# ADR-001: Postgres Over SQLite for State Store

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** Spark Engineering

## Context

V1 used a hybrid state store: SQLite WAL for jobs, JSON files on disk for session state, and in-memory dicts for active sessions. This caused:
- State drift between processes (gateway vs subprocesses)
- No crash recovery (in-memory state lost on restart)
- Concurrency issues with SQLite under parallel writes
- No LISTEN/NOTIFY for real-time approval flows

## Decision

Use a single PostgreSQL instance as the source of truth for all state: sessions, messages, tool_calls, jobs, workspaces, and gpu_nodes.

## Consequences

**Positive:**
- Single source of truth — no drift between processes
- Crash recovery via WAL (Postgres default)
- LISTEN/NOTIFY enables durable approval flows without in-memory Events
- JSONB columns allow flexible schema evolution without migrations
- Procrastinate (Postgres-backed queue) eliminates Redis dependency
- Better concurrency with row-level locking

**Negative:**
- Additional service to run (Postgres container)
- Slightly higher operational complexity vs SQLite file
- Requires connection pooling (asyncpg) for async Python

**Mitigations:**
- Docker Compose manages Postgres lifecycle
- asyncpg connection pool with configurable limits
- Single instance sufficient for 2-GPU home rig

## Alternatives Considered

1. **SQLite with WAL** — simpler but no LISTEN/NOTIFY, poor multi-process concurrency
2. **Redis** — good for queues but not for durable relational state
3. **DuckDB** — analytical workload, not transactional
4. **MongoDB** — document store doesn't enforce schema consistency
