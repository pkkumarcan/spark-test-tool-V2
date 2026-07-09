# X05 — Model Registry

**Purpose:** Understand which LLM models are available and how to manage them.  
**Estimated time:** 15 minutes

---

## Available Models

Spark V2 uses Ollama for LLM inference. Models are pulled from the Ollama registry.

### Default Models

| Model | Size | VRAM | Use Case | Quality |
|-------|------|------|----------|---------|
| `qwen3:8b` | 5 GB | ~6 GB | General purpose, coding, chat | Good |
| `qwen3:14b` | 9 GB | ~10 GB | Complex reasoning, research | Better |
| `qwen3:4b-instruct` | 3 GB | ~4 GB | Fast responses, simple tasks | Basic |

### Vision Models

| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| `llama3.2-vision:11b` | 7 GB | ~8 GB | Image understanding |
| `llava` | 5 GB | ~6 GB | Image description |
| `minicpm-v` | 5 GB | ~6 GB | Multimodal |

### Model Selection Logic

The agent runtime automatically selects models based on task:

1. **Pipeline stages** use `qwen3:8b` by default
2. **Coding agent** uses the model specified in the session
3. **Vision tasks** auto-switch to a vision model when images are attached
4. **If preferred model unavailable**, falls back to first available 8B/7B model

### Managing Models

```bash
# List installed models
ollama list

# Pull a new model
ollama pull qwen3:14b

# Remove a model
ollama rm qwen3:4b-instruct

# Check model info
ollama show qwen3:8b
```

### Adding Custom Models

1. Pull the model: `ollama pull <model-name>`
2. No code changes needed — Ollama auto-registers it
3. The agent will discover it automatically

---

## ComfyUI Models

ComfyUI uses separate model files for image/video generation:

| Model | Path | Purpose |
|-------|------|---------|
| flux1-schnell-q8.gguf | ComfyUI models/ | Image generation |
| t5xxl_fp8_e4m3fn.safetensors | ComfyUI models/ | Text encoder |
| clip_l.safetensors | ComfyUI models/ | CLIP encoder |
| ae.safetensors | ComfyUI models/ | VAE decoder |

Models are stored in the ComfyUI installation directory on the host.

---

## Model Performance Tips

- **Use 8B models** for pipeline stages (faster, good enough quality)
- **Use 14B models** for research and complex reasoning
- **Use vision models** only when images are attached (they're slower)
- **Pre-pull models** before running pipelines to avoid delays
- **Monitor VRAM** with `nvidia-smi` — if OOM, reduce context length or use smaller model
