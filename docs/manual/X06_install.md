# X06 — Installation Guide

**Purpose:** Step-by-step installation from fresh Ubuntu system.  
**Estimated time:** 30 minutes

---

## Prerequisites

### 1. Install Docker

```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Install NVIDIA Drivers

```bash
# Check if drivers are already installed
nvidia-smi

# If not installed:
sudo apt install nvidia-driver-535
sudo reboot
```

### 3. Install NVIDIA Container Toolkit

```bash
# Add the repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 4. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve &

# Pull the default model
ollama pull qwen3:8b
```

### 5. Install ComfyUI

```bash
# Clone ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI
cd ~/ComfyUI

# Install dependencies
pip install -r requirements.txt

# Start ComfyUI
python main.py --listen 0.0.0.0 --port 8188 &

# Download models (Flux schnell for image generation)
# Place model files in ~/ComfyUI/models/
```

---

## Install Spark V2

```bash
# Clone the repo
git clone <repo-url> ~/spark-test-tool-V2
cd ~/spark-test-tool-V2

# Configure environment
cp .env.example .env

# Edit .env — set at minimum:
# SPARK_API_KEY=your-secret-key
# SPARK_DEBUG=true  (for development)

# Start everything
./start.sh
```

The `start.sh` script:
1. Starts PostgreSQL and waits for it to be healthy
2. Runs database migrations
3. Starts all services (gateway, web, whisper, media-workers, f5-tts)

---

## Verify Installation

```bash
# Check all containers are running
docker compose -f infra/docker-compose.yml ps

# Check health endpoint
curl http://localhost:8080/health

# Check Web UI
open http://localhost:3002

# Check Ollama
curl http://localhost:11434/api/tags

# Check ComfyUI
curl http://localhost:8188/system_stats
```

---

## Configuration Reference

### `.env` Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SPARK_API_KEY` | (empty) | Yes | API authentication key |
| `SPARK_DEBUG` | `false` | No | Enable debug mode (disables auth requirement) |
| `SPARK_POSTGRES_URL` | `postgresql://spark:spark@localhost:5432/spark` | No | Database connection |
| `SPARK_OLLAMA_BASE_URL` | `http://localhost:11434` | No | Ollama API URL |
| `SPARK_DEFAULT_MODEL` | `qwen3:8b` | No | Default LLM model |
| `SPARK_COMFYUI_URL` | `http://localhost:8188` | No | ComfyUI API URL |
| `SPARK_CORS_ORIGINS` | `["http://localhost:3002"]` | No | Allowed CORS origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8080` | No | Frontend API base URL |

---

## Development Setup

For running without Docker (development):

```bash
# Backend
cd apps/gateway
pip install -e .
SPARK_DEBUG=true uvicorn apps.gateway.main:app --reload --port 8000

# Frontend
cd apps/web
npm install
npm run dev

# Tests
pytest tests/ -v
```

---

## Updating

```bash
cd ~/spark-test-tool-V2
git pull

# Rebuild containers
docker compose -f infra/docker-compose.yml build

# Restart
docker compose -f infra/docker-compose.yml up -d
```
