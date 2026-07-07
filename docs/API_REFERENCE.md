# Spark Media Factory V2 — API Reference

Base URL: `http://localhost:8000`

All `/api/*` endpoints require `X-API-Key` header when `SPARK_API_KEY` is set.

---

## System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (all services) |
| GET | `/api/gpu/status` | GPU utilization stats (Node A + Node B) |
| GET | `/output/{filename}` | Serve output file |

---

## Text

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/text/chat` | Plain chat completion |
| POST | `/api/text/enhance` | Enhance/rewrite text |
| GET | `/api/text/models` | List available LLM models |

**POST /api/text/chat**
```json
{
  "message": "Hello",
  "model": "qwen3:8b",
  "session_id": "optional-session-id",
  "context": "Default",
  "history": [],
  "images": [],
  "active_contexts": []
}
```

---

## Image

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/image/generate` | Generate image (FLUX/Z-Image) |

**POST /api/image/generate**
```json
{
  "prompt": "A futuristic cityscape",
  "negative_prompt": "blurry, low quality",
  "steps": 8,
  "width": 1024,
  "height": 1024,
  "model": "flux1-schnell-q8.gguf",
  "seed": null
}
```

---

## Video

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/video/generate` | Generate video (background job) |
| POST | `/api/video/test-frame` | Generate test frame |

---

## Audio

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/audio/transcribe` | Transcribe audio (Whisper) |
| POST | `/api/audio/speak` | Text-to-speech (F5-TTS) |
| POST | `/api/tts/synthesize` | TTS (alternate path) |
| POST | `/api/stt/transcribe` | STT (alternate path) |

---

## 3D Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/3d/generate` | Generate 3D asset |

---

## Music

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/music/generate` | Generate music (ACE-Step) |

---

## Extraction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/extract/ocr` | OCR from image |
| POST | `/api/extract/pdf` | Extract text from PDF |
| POST | `/api/extract/link` | Extract content from URL |
| POST | `/api/extract/youtube` | Extract YouTube transcript |

---

## RAG (Retrieval-Augmented Generation)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rag/sources` | List RAG sources |
| POST | `/api/rag/ingest` | Ingest text into RAG |
| POST | `/api/rag/query` | Query RAG |
| POST | `/api/rag/delete-source` | Delete a source |
| POST | `/api/rag/clear-all` | Clear all RAG data |

---

## Post-Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/postprocess/upscale` | Upscale image (Topaz) |
| POST | `/api/postprocess/lipsync` | Lip-sync video |

---

## Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | List recent jobs |
| GET | `/api/jobs/{job_id}` | Get job status |
| POST | `/api/jobs/{job_id}/cancel` | Cancel a job |
| DELETE | `/api/jobs/{job_id}` | Cancel job (V1 compat) |

---

## Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pipeline/run` | Run batch pipeline (Phase 1) |
| POST | `/api/pipeline/approve/{job_id}` | Approve and run Phase 2 |
| POST | `/api/pipeline/reject/{job_id}` | Reject pipeline job |
| GET | `/api/pipeline/status/{job_id}` | Get pipeline state |
| GET | `/api/pipeline/brief/{job_id}` | Get intelligence brief |
| GET | `/api/pipeline/script/{job_id}` | Get master script |
| GET | `/api/pipeline/topic/{job_id}` | Get selected topic |
| POST | `/api/pipeline/regenerate-field` | Regenerate a field via LLM |
| POST | `/api/pipeline/export` | Save exported content |
| GET | `/api/pipeline/download` | Download file from pipeline |
| GET | `/api/pipeline/assets/{job_id}` | List pipeline assets |
| GET | `/api/pipeline/jobs` | List all pipeline jobs |
| POST | `/api/pipeline/create` | Create V2 pipeline |
| GET | `/api/pipeline/list` | List V2 pipelines |
| GET | `/api/pipeline/{pipeline_id}` | Get V2 pipeline |
| POST | `/api/pipeline/{pipeline_id}/approve` | Approve V2 pipeline |
| POST | `/api/pipeline/{pipeline_id}/run` | Run V2 pipeline |
| POST | `/api/pipeline/{pipeline_id}/run-stage/{stage}` | Run specific stage |

---

## Publishing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/publish/upload` | Upload video (mock) |
| GET | `/api/publish/schedule` | Get publish schedule |
| POST | `/api/publish/schedule` | Schedule video |
| GET | `/api/publish/scheduler/queue` | List scheduler queue |
| POST | `/api/publish/scheduler/add` | Add to scheduler |
| POST | `/api/publish/scheduler/cancel/{job_id}` | Cancel scheduled job |

---

## Research & Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/research/generate` | Generate research |
| GET | `/api/assets` | List all generated assets |
| GET | `/api/research/files` | List research documents |
| GET | `/api/research/file` | Get research file content |
| POST | `/api/research/compile` | Compile research brief |
| POST | `/api/research/expand` | Expand research files |

---

## Gems

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/curate/generate` | Smart curation |
| POST | `/api/chain/generate` | Story chain generation |
| POST | `/api/moa/chat` | Mixture of Agents |
| POST | `/api/meme/generate` | Meme generator |
| POST | `/api/gems/finance` | Financial analyst |
| POST | `/api/gems/mcp` | MCP AI agent |
| POST | `/api/gems/ingest-source` | Ingest data source |
| POST | `/api/gems/chat-source` | Chat with data source |
| POST | `/api/gems/voice` | Voice AI agent |
| POST | `/api/gems/generate-ui` | Generative UI |
| POST | `/api/dify/run-workflow` | Dify workflow |
| POST | `/api/gems/coding-agent` | Coding agent (non-SSE) |

---

## Coding Agent (Stateful SSE)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orchestrator/code/stream` | SSE streaming agent |
| POST | `/api/orchestrator/code/approve` | Approve tool call |
| POST | `/api/orchestrator/code/reject` | Reject tool call |
| GET | `/api/orchestrator/code/memory` | Get agent memory |
| POST | `/api/orchestrator/code/memory` | Update agent memory |
| GET | `/api/orchestrator/code/replay/{session_id}` | Session replay |
| POST | `/api/orchestrator/code/multi-agent` | Multi-agent coding (SSE) |

---

## Orchestrator

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orchestrator/chat` | Chat-first orchestrator |

---

## IDE

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ide/files` | List workspace files |
| GET | `/api/ide/file` | Read file content |
| POST | `/api/ide/file` | Write file content |
| GET | `/api/ide/workspace` | Get workspace root |
| POST | `/api/ide/workspace` | Set workspace root |

---

## KPI Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/kpi/dashboard` | KPI dashboard |
| GET | `/api/kpi/experiments` | List experiments |
| POST | `/api/kpi/experiments` | Create experiment |

---

## Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/summary` | Session metrics aggregate |

---

## Mail Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mail/sync/start` | Start email sync |
| GET | `/api/mail/folders` | List mail folders |
| POST | `/api/mail/sync/stop` | Stop email sync |
| GET | `/api/mail/stats` | Mail statistics |
| GET | `/api/mail/emails` | List emails |
| POST | `/api/mail/cleanup` | Start cleanup |
| GET | `/api/mail/cleanup/preview` | Cleanup preview |
| GET | `/api/mail/senders` | List senders |
| POST | `/api/mail/stage-sender` | Stage sender |
| POST | `/api/mail/stage-senders` | Stage multiple senders |
| POST | `/api/mail/empty-trash` | Empty trash |
| POST | `/api/mail/deep-purge` | Deep purge |
| POST | `/api/mail/keyword-purge` | Keyword purge |
| GET | `/api/mail/keyword-search` | Keyword search |
