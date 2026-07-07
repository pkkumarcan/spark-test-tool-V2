# ADR-004: Docker Container Sandboxing for Tool Execution

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** Spark Engineering

## Context

V1 used regex allowlists and path validation for security:
- `workspace.py` checked file paths against allowed directories
- Command allowlists restricted shell commands
- No isolation between tool executions
- Agent could potentially escape sandbox via file system traversal

This approach doesn't close the actual security hole — regex patterns can be bypassed, and there's no process-level isolation.

## Decision

Execute all agent tool calls inside locked-down Docker containers with:
- `--network=none` — no network access (except web_search tool)
- Read-only root filesystem
- Writable tmpfs at `/tmp` (100MB limit)
- Workspace volume mounted read-write
- `no-new-privileges` security option
- Memory limit (512MB) and CPU limit (1 core)

## Consequences

**Positive:**
- True process isolation — agent cannot escape to host
- Network isolation prevents data exfiltration
- Resource limits prevent OOM/DoS
- Each tool execution is ephemeral — no state leakage between calls
- Deterministic environment (python:3.12-slim base image)

**Negative:**
- Docker daemon dependency (must be running)
- Slight overhead for container startup (~100ms)
- Workspace must be volume-mounted (not overlay)
- Some tools need network access (web_search) — handled via per-tool policy

**Mitigations:**
- Docker is already required for the deployment model
- Container reuse/pooling can reduce startup overhead
- Per-tool SandboxPolicy allows network access when needed
- Fallback to subprocess execution for development (no Docker)

## Alternatives Considered

1. **Regex allowlists** — V1 approach, bypassable
2. **gVisor** — stronger isolation but heavier, requires kernel support
3. **Firecracker** — microVMs, too complex for this use case
4. **nsjail/seccomp** — lighter but less isolation than Docker
5. **WASM sandbox** — limited tool compatibility
