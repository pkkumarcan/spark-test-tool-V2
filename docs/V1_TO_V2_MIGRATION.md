# V1 to V2 Migration Guide

## What Changed

### Architecture

| Aspect | V1 | V2 |
|--------|----|----|
| Backend | Single `main.py` (2180 lines) + 40 files | Modular monorepo: gateway, agent-runtime, media-workers |
| State Store | SQLite + JSON files + in-memory dicts | PostgreSQL (single source of truth) |
| Job Queue | SQLite + `asyncio.create_task()` | Procrastinate (Postgres-backed) |
| Agent Loop | Nested if/elif, regex JSON parsing | Explicit state machine + native tool-calling |
| Frontend | Single HTML + hand-rolled JS | Next.js + TypeScript + Tailwind |
| Security | Regex allowlists | Docker container sandbox |
| GPU Control | Flat `Semaphore(2)` | VRAM-aware scheduling per node |
| LLM Client | Ollama-only | Multi-provider abstraction |
| Observability | Langfuse only | OpenTelemetry + Langfuse as exporter |
| Deployment | Single Docker Compose | Multi-service + GPU node config |

### API Routes

All V1 endpoints are preserved in V2 with the same paths. Some additions:

- `GET /api/text/models` — list available LLM models
- `POST /api/text/enhance` — text enhancement
- `GET /api/gpu/status` — GPU utilization stats
- `GET /api/ide/files` — workspace file listing
- `GET /api/ide/file` — read file content
- `POST /api/ide/file` — write file content
- `GET /api/metrics/summary` — session metrics
- `GET /api/orchestrator/code/memory` — get agent memory
- `POST /api/orchestrator/code/memory` — set agent memory
- `GET /api/orchestrator/code/replay/{session_id}` — session replay

### Frontend Pages

| V1 Page | V2 Page |
|---------|---------|
| `index.html` | `app/page.tsx` (Dashboard) |
| `ide.html` | `app/ide/page.tsx` |
| `pipeline_dashboard.html` | `app/pipeline/page.tsx` |
| `pipeline_v2.html` | `app/pipeline/v2/page.tsx` |
| `mail.html` | `app/mail/page.tsx` |
| `preview.html` | `app/preview/page.tsx` |
| `simulator.html` | `app/simulator/page.tsx` |
| (new) | `app/chat/page.tsx` |

## How to Run V2

### Prerequisites

- Docker and Docker Compose
- NVIDIA GPU drivers (for media generation)
- Ollama running locally (for LLM inference)

### Quick Start

```bash
cd spark-test-tool-V2

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
./start.sh

# Or manually:
docker compose up -d
```

### Environment Variables

Key variables in `.env`:

```bash
# Postgres
SPARK_POSTGRES_URL=postgresql://spark:spark@localhost:5432/spark

# LLM
SPARK_OLLAMA_BASE_URL=http://host.docker.internal:11434
SPARK_DEFAULT_MODEL=qwen3:8b

# ComfyUI
SPARK_COMFYUI_URL=http://host.docker.internal:8188

# Security
SPARK_API_KEY=your-api-key
SPARK_CORS_ORIGINS=["http://localhost:3000"]

# Observability (optional)
SPARK_OTEL_ENABLED=true
SPARK_LANGFUSE_URL=https://your-langfuse-instance.com
SPARK_LANGFUSE_KEY=your-key
```

### Service Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Next.js Web   │────▶│   FastAPI Gateway │────▶│   PostgreSQL    │
│   (port 3000)   │     │   (port 8000)     │     │   (port 5432)   │
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

### Development

```bash
# Backend development
cd apps/gateway
pip install -e .
uvicorn apps.gateway.main:app --reload --port 8000

# Frontend development
cd apps/web
npm install
npm run dev

# Run tests
pytest tests/ -v

# Lint and type check
ruff check .
mypy .
```

### Data Migration

V2 uses Postgres instead of SQLite. To migrate existing job data:

```bash
# Export from V1 SQLite
python -c "
import sqlite3, json
conn = sqlite3.connect('output/jobs.db')
conn.row_factory = sqlite3.Row
jobs = [dict(row) for row in conn.execute('SELECT * FROM jobs')]
with open('v1_jobs_export.json', 'w') as f:
    json.dump(jobs, f, indent=2)
"

# Import to V2 Postgres (after V2 is running)
python -c "
import json, asyncio, asyncpg

async def migrate():
    conn = await asyncpg.connect('postgresql://spark:spark@localhost:5432/spark')
    with open('v1_jobs_export.json') as f:
        jobs = json.load(f)
    for job in jobs:
        await conn.execute('''
            INSERT INTO jobs (id, kind, status, priority, payload, created_at)
            VALUES (\$1, \$2, \$3, 0, \$4, \$5)
            ON CONFLICT (id) DO NOTHING
        ''', job['job_id'], job.get('job_type', 'unknown'),
             job.get('status', 'pending'), json.dumps(job),
             job.get('created_at', 'now()'))
    await conn.close()

asyncio.run(migrate())
"
```

### Troubleshooting

**Postgres connection refused:**
```bash
docker compose logs postgres
# Ensure postgres container is running and healthy
```

**Ollama not reachable:**
```bash
# Verify Ollama is running on host
curl http://localhost:11434/api/tags
```

**GPU not detected:**
```bash
# Check NVIDIA drivers
nvidia-smi
# Ensure nvidia-container-toolkit is installed
```

**Frontend can't reach API:**
```bash
# Check CORS settings in .env
SPARK_CORS_ORIGINS=["http://localhost:3000"]
# Ensure gateway is running on port 8000
```
