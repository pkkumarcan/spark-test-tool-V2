# Spark Media Factory V2

AI-powered media generation and coding agent platform. Full replication of V1 with robust, improved, and simplified architecture.

## Quick Start

```bash
# Clone and configure
cd spark-test-tool-V2
cp .env.example .env
# Edit .env with your settings

# Start all services
./start.sh

# Or manually
docker compose up -d
```

**Services:**
- **Web UI**: http://localhost:3002
- **API Gateway**: http://localhost:8080
- **PostgreSQL**: localhost:5432

## Architecture

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

## Features

### Coding Agent (18 Tools)
- File operations (read, write, edit, create, delete, multi-replace)
- Search (regex, semantic, symbols)
- Shell commands (Docker sandbox)
- Git operations (status, diff, log)
- Diagnostics and test runner
- Web search (DuckDuckGo, Tavily)

### Media Generation
- **Image**: FLUX, Z-Image via ComfyUI
- **Video**: LTX, Wan, CogVideoX, Mochi via ComfyUI
- **Music**: ACE-Step
- **TTS**: F5-TTS
- **STT**: Whisper
- **3D Assets**: ComfyUI
- **Memes**: LLM + Pillow

### AI/LLM Features
- Intent routing (Gemma4)
- Chat with RAG augmentation
- Mixture of Agents (MoA)
- Financial analyst agent
- Voice agent (STT → LLM → TTS)
- Dify workflow integration
- MCP agent

### Pipeline System
- 2-phase content pipeline (Research → Production)
- Human-in-the-loop approval
- Per-channel job tracking
- VRAM-aware scheduling

### Frontend Pages
- **Dashboard**: Service health, GPU status, navigation
- **IDE**: Monaco editor + terminal + agent chat (SSE)
- **Pipeline**: Content pipeline management
- **Mail**: Email organization agent
- **Simulator**: Media generation playground
- **Preview**: Asset browser with preview
- **Chat**: Plain chat interface

## Configuration

Key environment variables (see `.env.example`):

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
SPARK_CORS_ORIGINS=["http://localhost:3002", "http://localhost:3000"]
```

## Development

```bash
# Backend
cd apps/gateway
pip install -e .
uvicorn apps.gateway.main:app --reload --port 8000

# Frontend (runs on http://localhost:3002)
cd apps/web
npm install
npm run dev

# Tests
pytest tests/ -v

# Lint & Type Check
ruff check .
mypy .
```

## API

Full API reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

Key endpoints:
- `GET /health` — Service health
- `POST /api/text/chat` — Chat completion
- `POST /api/image/generate` — Image generation
- `POST /api/video/generate` — Video generation
- `POST /api/orchestrator/code/stream` — SSE coding agent
- `GET /api/jobs` — List background jobs

## Project Structure

```
spark-test-tool-V2/
├── apps/
│   ├── gateway/          # FastAPI — auth, routing, CORS
│   ├── agent-runtime/    # State machine + LLM client
│   ├── media-workers/    # Image/video/audio generation
│   └── web/              # Next.js frontend
├── packages/
│   ├── schemas/          # Pydantic models
│   ├── tool-registry/    # Tool definitions + sandbox
│   └── telemetry/        # OpenTelemetry setup
├── infra/                # Docker Compose + Dockerfiles
├── tests/                # Unit + integration + golden tests
├── docs/                 # ADRs + migration guide + API ref
└── start.sh              # One-command startup
```

## Migration from V1

See [docs/V1_TO_V2_MIGRATION.md](docs/V1_TO_V2_MIGRATION.md) for:
- Architecture changes
- API route comparison
- Data migration steps
- Troubleshooting

## Documentation

### Manual (Comprehensive Operations Guide)
- [Manual Index](docs/manual/INDEX.md) — Master index of all 23 chapters
- [X00 Pipeline Architecture](docs/manual/X00_pipeline_architecture.md) — Content pipeline design
- [X01 Orientation](docs/manual/X01_orientation.md) — Quickstart guide
- [X02 System Architecture](docs/manual/X02_system_architecture.md) — Component design
- [X03 Hardware Requirements](docs/manual/X03_hardware.md) — GPU, CPU, RAM needs
- [X05 Model Registry](docs/manual/X05_model_registry.md) — LLM models
- [X06 Installation Guide](docs/manual/X06_install.md) — Step-by-step setup
- [X07 Operations Runbook](docs/manual/X07_operations_runbook.md) — Day-to-day ops
- [X08 Smoke Tests](docs/manual/X08_smoke_tests.md) — Test suite
- [X09 Logging & Observability](docs/manual/X09_logging.md) — Debugging
- [X10 Reliability](docs/manual/X10_reliability.md) — Failure handling
- [X11 Research Workflow](docs/manual/X11_research.md) — Content research
- [X12 RAG & Knowledge Base](docs/manual/X12_rag.md) — Semantic search
- [X21 STT (Whisper)](docs/manual/X21_stt.md) — Speech-to-text
- [X22 TTS (F5-TTS)](docs/manual/X22_tts.md) — Text-to-speech
- [X41 ComfyUI Integration](docs/manual/X41_comfyui.md) — Image/video generation
- [X42 Image Generation](docs/manual/X42_image_gen.md) — Keyframe generation
- [X51 Video Generation](docs/manual/X51_video.md) — Video assembly
- [X65 FFmpeg Cookbook](docs/manual/X65_ffmpeg.md) — FFmpeg commands
- [X71 Channel Setup](docs/manual/X71_channels.md) — 12 channels & publishing
- [X92 Security](docs/manual/X92_security.md) — Security model
- [X96 Costing & ROI](docs/manual/X96_costing.md) — Revenue projections
- [X98 Incident Response](docs/manual/X98_incidents.md) — Troubleshooting
- [Channels Reference](docs/CHANNELS_REFERENCE.md) — All 12 channels detailed

### Architecture Decision Records
- [ADR-001: Postgres Over SQLite](docs/adr/001-postgres-over-sqlite.md)
- [ADR-002: Native Tool-Calling](docs/adr/002-native-tool-calling.md)
- [ADR-003: Procrastinate Job Queue](docs/adr/003-procrastinate-job-queue.md)
- [ADR-004: Docker Sandbox](docs/adr/004-docker-sandbox.md)
- [ADR-005: Next.js Frontend](docs/adr/005-nextjs-frontend.md)
- [ADR-006: Sandbox Threat Model](docs/adr/006-sandbox-threat-model.md)

### Other
- [API Reference](docs/API_REFERENCE.md)
- [V1 to V2 Migration](docs/V1_TO_V2_MIGRATION.md)
