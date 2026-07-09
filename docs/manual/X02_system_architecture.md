# X02 — System Architecture

**Purpose:** Understand how all V2 components connect and communicate.  
**Estimated time:** 30 minutes

---

## High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Next.js Web   │────▶│   FastAPI Gateway │────▶│   PostgreSQL    │
│   (port 3002)   │     │   (port 8080)     │     │   (port 5432)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                          ▲
                              ▼                          │
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Agent Runtime   │────▶│  Procrastinate   │
                        │  (state machine) │     │  (job queue)     │
                        └──────────────────┘     └─────────────────┘
                                                       │
                                                       ▼
                                                ┌─────────────────┐
                                                │ Media Workers    │
                                                │ (image/video/...)│
                                                └─────────────────┘
```

---

## Component Details

### 1. Next.js Frontend (`apps/web/`)

**Purpose:** User interface for all interactions.  
**Port:** 3002  
**Tech:** Next.js 14, TypeScript, Tailwind CSS, Zustand state management

**Pages:**
| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/` | Service health, GPU status, navigation |
| IDE | `/ide` | Monaco editor + terminal + coding agent chat |
| Pipeline | `/pipeline` | Content pipeline management |
| Chat | `/chat` | Plain LLM chat |
| Mail | `/mail` | Email organization agent |
| Simulator | `/simulator` | Media generation playground |
| Preview | `/preview` | Asset browser with preview |

**Communication:** All API calls go through `apps/web/lib/api.ts` to the gateway.

### 2. FastAPI Gateway (`apps/gateway/`)

**Purpose:** API routing, authentication, CORS, rate limiting, job dispatch.  
**Port:** 8080 (mapped from container 8000)  
**Tech:** FastAPI, Pydantic, asyncpg

**Middleware stack (applied in order):**
1. `dynamic_cors` — per-request CORS headers
2. `BodySizeLimitMiddleware` — reject >10MB bodies
3. `APIKeyMiddleware` — validate `X-API-Key` header
4. `RateLimitMiddleware` — 100 requests/minute per IP

**Routes:**
| Router | Prefix | Purpose |
|--------|--------|---------|
| system | `/health`, `/api/gpu`, `/output` | Health, GPU status, file serving |
| agent | `/api/orchestrator/code` | Coding agent (SSE streaming) |
| chat | `/api/text` | Chat completion, enhance, models |
| media | `/api/image`, `/api/video`, `/api/audio` | Media generation |
| pipeline | `/api/pipeline` | Pipeline CRUD, run, approve |
| publish | `/api/publish` | YouTube upload |
| ide | `/api/ide` | File read/write, workspace listing |
| rag | `/api/rag` | Semantic search, document ingest |
| gems | `/api/gems` | Saved prompts/tools |
| kpi | `/api/kpi` | Performance metrics |
| metrics | `/api/metrics` | Session metrics |

### 3. Agent Runtime (`apps/agent-runtime/`)

**Purpose:** LLM-powered coding agent with tool-calling and state machine.  
**Tech:** Python, httpx, asyncpg

**Key files:**
| File | Purpose |
|------|---------|
| `state_machine.py` | Agent loop: PLANNING → TOOL_CALL → SANDBOX_EXEC → VERIFY → DONE |
| `llm_client.py` | Multi-provider LLM client (Ollama primary, vLLM fallback) |
| `pipeline.py` | Content pipeline state machine (9 stages) |
| `session.py` | Postgres-backed session persistence |
| `approval.py` | Human-in-the-loop approval via Postgres LISTEN/NOTIFY |
| `context.py` | Message compression for long conversations |
| `rag.py` | RAG query and document ingestion |
| `router.py` | Intent routing (chat vs. agent vs. pipeline) |

**Agent state machine:**
```
PLANNING → TOOL_CALL → SANDBOX_EXEC → VERIFY → (APPROVAL_PENDING) → DONE | FAILED
```

### 4. Tool Registry (`packages/tool_registry/`)

**Purpose:** Registered tools available to the coding agent.  
**Auto-discovery:** Imports all modules under `packages/tool_registry/tools/` on first access.

**Tools (18 total):**

| Category | Tools |
|----------|-------|
| File ops | `read_file`, `create_file`, `write_file`, `edit_file`, `multi_replace`, `delete_file`, `list_directory`, `make_directory` |
| Search | `search_files`, `semantic_search` |
| Shell | `run_command` |
| Git | `git_status`, `git_diff`, `git_log` |
| Analysis | `list_symbols`, `get_diagnostics`, `run_tests` |
| Security | `security_scan` |
| Meta | `done` |

**Sandbox enforcement:** `_policy_precheck` in `state_machine.py` validates every tool call against its declared `SandboxPolicy` before the handler runs.

### 5. Media Workers (`apps/media_workers/`)

**Purpose:** Execute media generation tasks (image, video, audio, 3D).  
**Tech:** httpx (ComfyUI API), subprocess (FFmpeg), asyncpg

| Worker | Purpose |
|--------|---------|
| `image.py` | Image generation via ComfyUI |
| `video.py` | Video generation via ComfyUI |
| `tts.py` | Text-to-speech via F5-TTS |
| `stt.py` | Speech-to-text via Whisper |
| `music.py` | Music generation via ACE-Step |
| `three_d.py` | 3D asset generation |
| `meme.py` | Meme generation via LLM + Pillow |
| `extraction.py` | Audio/text extraction from media |
| `postprocess.py` | Video post-processing |
| `publishing.py` | YouTube upload |
| `comfyui_client.py` | ComfyUI API client |
| `vram_tracker.py` | GPU VRAM monitoring |
| `scheduler.py` | Job scheduling with VRAM awareness |
| `sandbox.py` | Container sandbox for tool execution |

### 6. PostgreSQL

**Purpose:** Single source of truth for sessions, messages, tool calls, jobs.  
**Port:** 5432  
**Image:** postgres:16-alpine

**Tables:**
| Table | Purpose |
|-------|---------|
| `sessions` | Agent/chat sessions |
| `messages` | Conversation history |
| `tool_calls` | Tool execution records |
| `jobs` | Background media jobs |
| `approvals` | Human approval decisions |

---

## Data Flow

### Coding Agent Request
```
User types in IDE → Next.js → POST /api/orchestrator/code/stream
→ Gateway → AgentStateMachine.run()
→ LLM chat (Ollama) → tool call → sandbox precheck → tool handler
→ result back to LLM → response via SSE → Next.js renders
```

### Pipeline Request
```
User clicks "Launch Pipeline" → Next.js → POST /api/pipeline/create
→ Gateway → create_pipeline() → POST /api/pipeline/{id}/run
→ Gateway → PipelineRunner.run_full() (async)
→ Stage: TOPIC → Ollama generates brief → Stage: SCRIPT → ...
→ Stage: APPROVAL → pauses for human → Stage: VOICEOVER → F5-TTS
→ Stage: VISUALS → ComfyUI → Stage: STITCH → FFmpeg → publish
```

### Media Generation Request
```
User in Simulator → Next.js → POST /api/image/generate
→ Gateway → dispatches to media-workers → ComfyUI API
→ Image saved to /output/ → returned to frontend
```

---

## Security Model

See [X92 Security](X92_security.md) for full details.

**Layers:**
1. **API Key** — `hmac.compare_digest` constant-time comparison
2. **Rate limiting** — 100 req/min per IP (in-memory, single instance)
3. **Sandbox policy** — per-tool filesystem/network restrictions
4. **Path containment** — `is_within_root()` prevents traversal
5. **Command allow-list** — only approved binaries can execute
6. **Docker isolation** — tool execution in containers (planned)

---

## Key Design Decisions

See `docs/adr/` for full ADRs:

| ADR | Decision | Rationale |
|-----|----------|-----------|
| 001 | PostgreSQL over SQLite | Multi-service, concurrent access, LISTEN/NOTIFY |
| 002 | Native tool-calling | Better than regex parsing, Ollama supports it |
| 003 | Procrastinate job queue | Postgres-backed, reliable, no extra infra |
| 004 | Docker container sandbox | True process isolation (planned) |
| 005 | Next.js frontend | SSR, TypeScript, Tailwind, component ecosystem |
| 006 | Sandbox threat model | Documents what each security layer protects |
