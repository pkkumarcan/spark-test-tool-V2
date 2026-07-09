# X01 — Orientation & Quickstart

**Purpose:** Get Spark V2 running and verify the first end-to-end pipeline.  
**Estimated time:** 20 minutes  
**Prerequisites:** Docker, NVIDIA GPU + drivers, Ollama on host

---

## What Is Spark V2?

Spark Media Factory V2 is an AI-powered content production platform that automates YouTube video creation across 12 niche channels. It takes a topic, generates research briefs, writes scripts, synthesizes voiceover, generates visuals via ComfyUI, assembles the final video, and publishes it.

**Architecture in one line:** Next.js frontend → FastAPI gateway → PostgreSQL → Agent runtime (state machine) → Media workers (ComfyUI, F5-TTS, FFmpeg)

---

## Quick Start

```bash
cd spark-test-tool-V2

# 1. Configure
cp .env.example .env
# Edit .env (see X06 for details)

# 2. Start everything
./start.sh

# 3. Open the UI
# Browser → http://localhost:3002
```

**Services started:**
| Service | Port | Purpose |
|---------|------|---------|
| Web UI | 3002 | Next.js frontend |
| Gateway | 8080 | FastAPI API server |
| PostgreSQL | 5432 | Database |
| Whisper | 10300 | Speech-to-text |
| Media Workers | — | Image/video generation |
| F5-TTS | 9880 | Text-to-speech |

---

## Verify It Works

### 1. Health Check
```bash
curl http://localhost:8080/health
# Expected: {"services": {"postgres": "online", "ollama": "online", ...}}
```

### 2. Web UI
Open http://localhost:3002 — you should see the Dashboard with service status cards.

### 3. Launch a Pipeline
1. Navigate to http://localhost:3002/pipeline
2. Click **"How It Works"** to read the guide
3. Select channel **MLN** (Macro Lens)
4. Type topic: **"AI Agent Infrastructure 2026"**
5. Click **"Launch Pipeline"**
6. Watch the job appear in the table with status `running`

### 4. Coding Agent
1. Navigate to http://localhost:3002/ide
2. Type: **"Create a Python hello world script"**
3. The agent will create the file and show the result

---

## First-Time Checklist

- [ ] Docker Engine running (`docker info`)
- [ ] NVIDIA GPU available (`nvidia-smi`)
- [ ] Ollama running on host (`curl http://localhost:11434/api/tags`)
- [ ] ComfyUI running on host (`curl http://localhost:8188/system_stats`)
- [ ] `.env` configured (at minimum: `SPARK_API_KEY`)
- [ ] `./start.sh` completed without errors
- [ ] Health check returns all services online
- [ ] Web UI accessible at http://localhost:3002

---

## Common First-Run Issues

| Problem | Fix |
|---------|-----|
| `docker: permission denied` | Run `sudo usermod -aG docker $USER` then re-login |
| `nvidia-smi` not found | Install NVIDIA drivers: `sudo apt install nvidia-driver-535` |
| Ollama not reachable | Start Ollama: `ollama serve` |
| Port 5432 in use | Stop local Postgres: `sudo systemctl stop postgresql` |
| Gateway exits immediately | Check `SPARK_API_KEY` is set in `.env` |
| Web UI blank | Check `NEXT_PUBLIC_API_URL=http://localhost:8080` in `.env` |

---

## Next Steps

- Read [X02 System Architecture](X02_system_architecture.md) to understand how components connect
- Read [X06 Installation Guide](X06_install.md) for detailed setup
- Read [X00 Pipeline Architecture](X00_pipeline_architecture.md) to understand the content pipeline
