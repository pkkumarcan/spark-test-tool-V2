# X92 — Security

**Purpose:** Security model, hardening, and best practices.  
**Estimated time:** 20 minutes

---

## Security Layers

Spark V2 implements defense-in-depth with multiple overlapping layers:

```
Layer 1: API Key Authentication (hmac.compare_digest)
Layer 2: Rate Limiting (100 req/min per IP)
Layer 3: Sandbox Policy Pre-check (per-tool validation)
Layer 4: Path Containment (is_within_root)
Layer 5: Command Allow-list (shell.py)
Layer 6: Container Isolation (planned, ADR-004)
```

---

## Layer 1: API Key Authentication

**File:** `apps/gateway/middleware.py`

```python
import hmac
key = request.headers.get("x-api-key", "")
if not hmac.compare_digest(key, self.api_key):
    return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key."})
```

- Constant-time comparison prevents timing attacks
- `SPARK_API_KEY` must be set in production
- Health endpoints (`/health`, `/docs`) are exempt

**Startup guard:**
```python
if not settings.debug and not settings.api_key:
    raise RuntimeError("SPARK_API_KEY must be set when SPARK_DEBUG is False")
```

---

## Layer 2: Rate Limiting

**File:** `apps/gateway/middleware.py`

- 100 requests per minute per client IP
- In-memory token bucket (single instance only)
- Health endpoints exempt

**Note:** For multi-replica deployments, move to Redis.

---

## Layer 3: Sandbox Policy Pre-check

**File:** `apps/agent-runtime/state_machine.py`

Before every tool handler runs:
```python
def _policy_precheck(tool_def, tool_args: dict) -> str | None:
    policy = tool_def.sandbox_policy
    if "path" in tool_args and policy.filesystem_scope != "":
        if not _sandbox.validate_path(str(tool_args["path"]), policy):
            return "Permission denied. Target path lies outside sandbox."
    if "command" in tool_args and not policy.network_access:
        if not _sandbox.validate_command(str(tool_args["command"]), policy):
            return "Permission denied. Command requires network access."
    return None
```

---

## Layer 4: Path Containment

**File:** `packages/tool_registry/paths.py`

```python
def is_within_root(path: str, root: str) -> bool:
    root = os.path.realpath(root)
    resolved = os.path.realpath(path) if os.path.isabs(path) else os.path.realpath(os.path.join(root, path))
    return resolved == root or resolved.startswith(root + os.sep)
```

- Uses `os.path.realpath()` to resolve symlinks
- Checks for `root + os.sep` boundary (prevents `/workspace-evil` bypass)
- Single source of truth — all tools import from `paths.py`

---

## Layer 5: Command Allow-List

**File:** `packages/tool_registry/tools/shell.py`

```python
ALLOWED_COMMANDS = {
    "python", "python3", "pip", "pytest", "ruff", "black", "mypy", "py_compile",
    "node", "npm", "npx", "yarn", "pnpm", "bun", "vite", "tsc", "eslint", "prettier",
    "cargo", "rustc", "go",
    "ls", "cat", "echo", "head", "tail", "wc", "find", "grep", "sed", "awk",
    "sort", "uniq", "diff", "tee", "xargs", "mkdir", "cp", "mv", "touch", "cd",
    "git",
    "which", "env", "date", "uname",
}
```

- `docker` and `docker-compose` are NOT in the allow-list
- Commands are blocked before execution via `shlex.split` + allow-list check
- `_audit_command` catches dangerous patterns (curl|bash, /etc/passwd, etc.)

---

## Security Best Practices

### Deployment
1. **Always set `SPARK_API_KEY`** in production
2. **Don't expose PostgreSQL** to the internet (port 5432)
3. **Use HTTPS** in production (reverse proxy with Let's Encrypt)
4. **Don't mount Docker socket** into containers
5. **Run containers with `--network=none`** for untrusted tool execution

### Development
1. Use `SPARK_DEBUG=true` only in local development
2. Don't commit `.env` files
3. Use strong, unique API keys
4. Review tool call logs regularly

### Pipeline
1. Review scripts before approving at the APPROVAL gate
2. Monitor pipeline outputs for unexpected content
3. Audit shell commands via `_audit_command` logs

---

## Threat Model

See `docs/adr/006-sandbox-threat-model.md` for full threat model.

**Key insight:** String matching (command allow-list, audit regexes) is NOT network isolation. True network isolation requires `--network=none` at the container level (planned in ADR-004).
