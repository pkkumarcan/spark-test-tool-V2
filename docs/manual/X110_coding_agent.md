# X110 — Coding Agent

**Purpose:** 18-tool coding agent with state machine, sandbox enforcement, and human approval.  
**Created:** 2026-07-09 (V3 — V2 agent integration docs)  
**Estimated time:** 20 minutes

---

## Overview

The coding agent is an autonomous AI assistant that can read, write, edit, search, and execute code. It uses a state machine loop with tool-calling, sandbox enforcement, and human-in-the-loop approval for dangerous operations.

---

## Architecture

```
User Prompt → LLM (Ollama) → Tool Call → Sandbox Precheck → Tool Handler → Result → LLM → Response
     ↑                                                                          |
     └──────────────────────────────────────────────────────────────────────────┘
                              (loop until done)
```

### State Machine

```
PLANNING → TOOL_CALL → SANDBOX_EXEC → VERIFY → (APPROVAL_PENDING) → DONE | FAILED
```

| State | Description |
|-------|-------------|
| PLANNING | LLM decides next action (text response or tool call) |
| TOOL_CALL | Validates tool exists, prepares arguments |
| SANDBOX_EXEC | Runs policy precheck, executes handler |
| VERIFY | Checks result, decides next state |
| APPROVAL_PENDING | Pauses for human approval (dangerous tools) |
| DONE | Task complete |
| FAILED | Error occurred |

---

## Available Tools (18)

### File Operations
| Tool | Description | Approval Required |
|------|-------------|-------------------|
| `read_file` | Read file contents with optional line range | No |
| `create_file` | Create new file (fails if exists) | Yes |
| `write_file` | Write/overwrite file content | Yes |
| `edit_file` | Surgical text replacement (old→new) | Yes |
| `multi_replace` | Multiple non-contiguous replacements | Yes |
| `delete_file` | Delete a file | Yes |
| `list_directory` | List directory contents | No |
| `make_directory` | Create directory | Yes |

### Search & Analysis
| Tool | Description | Approval Required |
|------|-------------|-------------------|
| `search_files` | Regex search file contents | No |
| `semantic_search` | RAG-based semantic search | No |
| `list_symbols` | AST parse Python file (classes, functions) | No |
| `get_diagnostics` | Run ruff/py_compile lint | No |
| `run_tests` | Run pytest | No |

### Shell & Git
| Tool | Description | Approval Required |
|------|-------------|-------------------|
| `run_command` | Execute shell command | Yes |
| `git_status` | Show git status | No |
| `git_diff` | Show git diff | No |
| `git_log` | Show git log | No |

### Other
| Tool | Description | Approval Required |
|------|-------------|-------------------|
| `security_scan` | Run bandit/pip-audit | No |
| `done` | Mark task complete | No |

---

## Sandbox Enforcement

### Policy Pre-Check

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

### Sandbox Layers

| Layer | Protection | Example |
|-------|-----------|---------|
| API Key | Authentication | `hmac.compare_digest` |
| Rate Limit | 100 req/min | Token bucket |
| Policy Pre-check | Per-tool validation | Filesystem scope, network access |
| Path Containment | `is_within_root()` | Prevents `/workspace-evil` bypass |
| Command Allow-list | Only approved binaries | No `docker`, `sudo`, etc. |

---

## Tool Call Flow

```
1. LLM returns tool_call: {"name": "read_file", "arguments": {"path": "test.py"}}
2. State machine: validate tool exists
3. State machine: check requires_approval → if yes, pause for human
4. State machine: run _policy_precheck(tool_def, tool_args)
   - If blocked → return error, skip handler
   - If OK → continue
5. Execute tool handler: result = tool_def.handler(**tool_args)
6. Return result to LLM for next planning step
```

---

## Human Approval

Tools with `requires_approval=True` pause at APPROVAL_PENDING state:

```
APPROVAL_PENDING → (human approves via dashboard) → SANDBOX_EXEC → handler runs
APPROVAL_PENDING → (human rejects) → VERIFY → error message back to LLM
```

**Approval is via Postgres LISTEN/NOTIFY:**
1. Tool call persisted to `approvals` table
2. SSE event sent to frontend
3. Human clicks Approve/Reject in dashboard
4. State machine unblocks and continues

---

## Stuck Loop Detection

```python
if len(recent_tool_calls) == 3 and len(set(recent_tool_calls)) == 1:
    consecutive_errors += 1
    if consecutive_errors >= 2:
        yield error("Stuck loop: repeated tool N times. Stopping.")
        state = FAILED
```

---

## LLM Client

**Primary:** Ollama (native tool-calling)  
**Fallback:** vLLM (OpenAI-compatible API)

```python
class LLMClient:
    def __init__(self, ollama_url: str, vllm_url: str | None = None):
        self.ollama_url = ollama_url
        self.vllm_url = vllm_url

    async def chat(self, messages, model, tools, stream, timeout, temperature):
        # Build Ollama payload with tools
        # Retry 3 times with exponential backoff
        # Parse response into LLMResponse(content, tool_calls, tokens_used)
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/orchestrator/code/stream` | POST | Start agent (SSE stream) |
| `/api/orchestrator/code/approve` | POST | Approve pending tool call |
| `/api/orchestrator/code/reject` | POST | Reject pending tool call |
| `/api/orchestrator/code/memory` | GET/POST | Get/set agent memory |
| `/api/orchestrator/code/replay/{session_id}` | GET | Replay session |

---

## Session Management

Sessions are stored in PostgreSQL:

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id TEXT DEFAULT 'default',
    kind TEXT DEFAULT 'agentic',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    role TEXT,  -- system | user | assistant | tool
    content TEXT,
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Usage Examples

### Via Dashboard
1. Navigate to IDE page
2. Type: "Create a Python hello world script"
3. Agent creates the file, shows result

### Via API
```bash
curl -X POST http://localhost:8080/api/orchestrator/code/stream \
  -H "Content-Type: application/json" \
  -d '{"task": "Fix the bug in main.py", "model": "qwen3:8b", "session_id": "my-session"}'
```

### Via Frontend
```typescript
const response = await sendAgentMessage(
  "Create a Python hello world script",
  "qwen3:8b",
  sessionId
);
// Response is SSE stream
```
