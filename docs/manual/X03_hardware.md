# X03 — Hardware Requirements

**Purpose:** Know what hardware is needed and recommended for Spark V2.  
**Estimated time:** 10 minutes

---

## Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 50 GB free | 200+ GB SSD |
| GPU | NVIDIA with 8GB VRAM | NVIDIA with 24+ GB VRAM |
| OS | Linux (Ubuntu 22.04+) | Ubuntu 22.04/24.04 |
| Docker | 24.0+ | 25.0+ |
| Docker Compose | v2.20+ | v2.24+ |

---

## GPU Requirements

Spark V2 uses GPU for:
- **LLM inference** (Ollama) — runs on host, not in container
- **Image generation** (ComfyUI/Flux) — runs on host, not in container
- **Video generation** (ComfyUI/LTX, Wan, CogVideoX) — runs on host
- **TTS** (F5-TTS) — runs in container with GPU access
- **STT** (Whisper) — runs in container with GPU access

**VRAM usage by model:**

| Model | VRAM | Purpose |
|-------|------|---------|
| qwen3:8b | ~6 GB | LLM inference |
| qwen3:14b | ~10 GB | LLM inference (better quality) |
| flux1-schnell-q8 | ~8 GB | Image generation |
| F5-TTS | ~4 GB | Text-to-speech |
| Whisper small | ~2 GB | Speech-to-text |

**Total peak VRAM:** ~30 GB (all running simultaneously)

### Single GPU Setup
If you have one GPU (e.g., RTX 3090 24GB or RTX 4090 24GB):
- Run Ollama and ComfyUI on the host (they share the GPU)
- F5-TTS and Whisper run in containers with GPU passthrough
- Use `--network=none` for containers that don't need network

### Dual GPU Setup
If you have two GPUs:
- GPU 0: Ollama (LLM inference)
- GPU 1: ComfyUI (image/video generation)
- F5-TTS and Whisper can share either GPU

### No GPU Setup
Without a GPU:
- LLM inference falls back to CPU (slow, ~10x slower)
- ComfyUI falls back to CPU (very slow for images/video)
- TTS/STT fall back to CPU (usable but slow)
- Pipeline will work but each stage takes much longer

---

## Network Requirements

| Port | Service | Direction |
|------|---------|-----------|
| 3002 | Web UI | Inbound (browser) |
| 8080 | API Gateway | Inbound (browser, other services) |
| 5432 | PostgreSQL | Internal only |
| 11434 | Ollama | Host (not containerized) |
| 8188 | ComfyUI | Host (not containerized) |
| 9880 | F5-TTS | Internal (container) |
| 10300 | Whisper | Internal (container) |

**Ollama and ComfyUI run on the host**, not in Docker containers. The gateway container reaches them via `host.docker.internal` (configured in docker-compose.yml).

---

## Storage Layout

```
spark-test-tool-V2/
├── output/              # Generated media files
│   └── jobs/            # Per-pipeline job outputs
│       └── pipe_*/      # Audio, visuals, final video per job
├── model-cache/         # Downloaded model weights
│   ├── F5TTS/           # F5-TTS model files
│   └── flux/            # ComfyUI model files
├── .env                 # Configuration (not committed)
└── infra/               # Docker configs
```

**Estimated storage per pipeline run:** 500MB-2GB (depending on video length and resolution)

---

## Environment Variables

Key variables (see `.env.example` for full list):

```bash
# Required
SPARK_API_KEY=your-secret-key       # API authentication
SPARK_POSTGRES_URL=postgresql://spark:spark@localhost:5432/spark

# LLM
SPARK_OLLAMA_BASE_URL=http://localhost:11434
SPARK_DEFAULT_MODEL=qwen3:8b

# ComfyUI
SPARK_COMFYUI_URL=http://localhost:8188

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8080

# Optional
SPARK_NODE_B_URL=                   # Remote GPU node
SPARK_LANGFUSE_URL=                 # Observability
SPARK_LANGFUSE_KEY=
```

---

## Pre-Flight Checklist

```bash
# Check Docker
docker --version          # >= 24.0
docker compose version    # >= 2.20

# Check GPU
nvidia-smi                # Should show GPU info

# Check Ollama
curl http://localhost:11434/api/tags   # Should return model list

# Check ComfyUI
curl http://localhost:8188/system_stats  # Should return stats

# Check disk space
df -h /                   # >= 50GB free

# Check ports
ss -tlnp | grep -E '5432|8080|3002'  # Should be free
```
