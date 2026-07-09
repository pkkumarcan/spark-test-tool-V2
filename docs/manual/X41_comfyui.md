# X41 — ComfyUI Integration

**Purpose:** How ComfyUI is used for image and video generation.  
**Estimated time:** 20 minutes

---

## Overview

ComfyUI is a node-based Stable Diffusion GUI that runs on the host (not in Docker). Spark V2 communicates with it via HTTP API.

**Service:** Runs on host  
**Port:** 8188  
**URL:** `http://localhost:8188` (from host) / `http://host.docker.internal:8188` (from containers)

---

## Architecture

```
Spark V2 (container) → HTTP API → ComfyUI (host) → GPU → Image/Video → /output/
```

1. Spark V2 sends a workflow JSON to ComfyUI's `/prompt` endpoint
2. ComfyUI executes the workflow on GPU
3. Spark V2 polls `/history/{prompt_id}` until complete
4. Output file is copied from ComfyUI output dir to Spark's output dir

---

## Image Generation Workflow

```json
{
  "prompt": {
    "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-schnell-q8.gguf"}},
    "11": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}},
    "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 576, "batch_size": 1}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "YOUR_PROMPT", "clip": ["11", 0]}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality", "clip": ["11", 0]}},
    "3": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "output", "images": ["8", 0]}}
  }
}
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/prompt` | POST | Submit a workflow for execution |
| `/history/{prompt_id}` | GET | Check execution status and get outputs |
| `/system_stats` | GET | System statistics (GPU, memory) |
| `/queue` | GET | Check pending queue |
| `/view?filename=X` | GET | Download generated image |

---

## Models Used

| Model | Type | Purpose |
|-------|------|---------|
| flux1-schnell-q8.gguf | UNet | Image generation (4 steps, fast) |
| t5xxl_fp8_e4m3fn.safetensors | CLIP | Text encoding |
| clip_l.safetensors | CLIP | Image encoding |
| ae.safetensors | VAE | Image decoding |

---

## ComfyUI Client

Located at `apps/media_workers/comfyui_client.py`:

```python
class ComfyUIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def submit_workflow(self, workflow: dict) -> str:
        """Submit workflow, return prompt_id"""

    async def wait_for_completion(self, prompt_id: str, timeout: int = 120) -> dict:
        """Poll until complete, return outputs"""

    async def get_output(self, filename: str) -> bytes:
        """Download generated file"""
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| ComfyUI not reachable | Not running on host | Start ComfyUI |
| OOM on GPU | Too many concurrent requests | Reduce batch size or use smaller model |
| Workflow timeout | Complex workflow | Increase timeout or simplify nodes |
| Model not found | Model file missing | Download model to ComfyUI models dir |
