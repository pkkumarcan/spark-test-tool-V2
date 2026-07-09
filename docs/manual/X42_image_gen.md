# X42 — Image Generation

**Purpose:** Keyframe and thumbnail generation via Stable Diffusion XL + Photopea.  
**Updated:** 2026-07-09 (V3 — SD XL on RTX 3090, Photopea for thumbnails)  
**Estimated time:** 15 minutes

---

## Overview

Image generation uses two tools:
1. **Stable Diffusion XL** (local on RTX 3090) — Keyframe generation
2. **Photopea** (web-based, free) — Thumbnail text overlays

---

## Keyframe Generation (SD XL)

### Setup
- ComfyUI running on host (port 8188)
- Models: flux1-schnell-q8.gguf, t5xxl, clip_l, ae.safetensors
- Resolution: 1024x576 (16:9) or 1024x1024 (square)

### Process
1. Construct prompt from script section narration
2. Submit workflow to ComfyUI API
3. Poll until complete
4. Copy output to job directory

### Prompt Construction
```python
def build_image_prompt(narration: str, channel_style: str) -> str:
    return f"{channel_style}. Cinematic documentary scene: {narration[:150]}. Professional lighting, 16:9."
```

### Channel Visual Styles

| Channel | Style Prompt |
|---------|-------------|
| DFW | "Anime cozy room, rain window, warm lighting, lofi aesthetic" |
| STM | "Ancient Roman philosopher, marble columns, golden hour, muted earth tones" |
| ODA | "Dark cinematic, archival footage aesthetic, dramatic shadows, mysterious" |
| PKP | "Clean clinical, data overlays, body/brain graphics, modern medical" |
| DKS | "Dark moody, silhouettes, dramatic lighting, psychological imagery" |
| GDB | "Maps, trade routes, satellite imagery, dark navy and gold palette" |
| ISL | "Warm golds, temple imagery, sacred geometry, calligraphy, nature" |
| NHZ | "Dark space, neon accents, particle effects, 3D renders, futuristic" |
| RMR | "Destination landscape, cost comparison graphics, warm travel aesthetic" |
| BWA | "Screen-share, terminal output, architecture diagrams, dark IDE theme" |

### ComfyUI Workflow
```json
{
  "prompt": {
    "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-schnell-q8.gguf"}},
    "11": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}},
    "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 576, "batch_size": 1}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "YOUR_PROMPT_HERE", "clip": ["11", 0]}},
    "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality, text artifacts", "clip": ["11", 0]}},
    "3": {"class_type": "KSampler", "inputs": {"seed": 42, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
    "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
    "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "keyframe", "images": ["8", 0]}}
  }
}
```

### Output Structure
```
output/jobs/pipe_abc12345/
├── visuals/
│   ├── keyframes/
│   │   ├── keyframe_00001_.png    # HOOK section
│   │   ├── keyframe_00002_.png    # INTRO section
│   │   ├── keyframe_00003_.png    # BODY section
│   │   └── keyframe_00004_.png    # CTA section
│   └── upscaled/
│       ├── S01_upscaled.png       # 1920x1080
│       └── ...
```

---

## Thumbnail Generation

### Process
1. Generate base image via SD XL (1280x720)
2. Open in Photopea (https://photopea.com)
3. Add bold text overlay (3-5 words max)
4. Export as PNG

### Thumbnail Rules
- **Face or emotional expression** when possible
- **3-5 words max** on thumbnail
- **High contrast** — readable at small size
- **Consistent branding** per channel
- **No clutter** — one focal point

### Photopea Batch Script
```javascript
// Photopea script for adding text overlay
var doc = app.activeDocument;
var textLayer = doc.artLayers.add();
textLayer.kind = LayerKind.TEXT;
textLayer.textItem.contents = "YOUR TITLE";
textLayer.textItem.size = 72;
textLayer.textItem.font = "ArialMT";
textLayer.textItem.color = new SolidColor();
textLayer.textItem.color.rgb.red = 255;
textLayer.textItem.color.rgb.green = 255;
textLayer.textItem.color.rgb.blue = 255;
textLayer.textItem.position = [200, 400];
```

### Fallback
If SD XL is unavailable, generate placeholder:
```bash
ffmpeg -y -f lavfi -i "color=c=#1a1a2e:s=1280x720:d=1" -vframes 1 thumbnail.png
```

---

## Per-Channel Image Counts

| Channel | Keyframes/Video | Notes |
|---------|----------------|-------|
| DFW | 1 (looping) | Single anime loop, 1-4 hours |
| STM | 8-12 | One per script section |
| ODA | 10-15 | Mystery reveals, dramatic |
| PKP | 8-10 | Clinical, data overlays |
| DKS | 8-12 | Dark, moody scenes |
| GDB | 8-10 | Maps, infographics |
| ISL | 6-8 | Temple, nature scenes |
| NHZ | 10-15 | Sci-fi, futuristic |
| RMR | 8-10 | Destination B-roll |
| BWA | 5-8 | Screen-shots, diagrams |

---

## Quality Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Steps | 4 | Fast mode (flux schnell) |
| CFG | 1.0 | Low for natural variation |
| Sampler | euler | Fast, good quality |
| Resolution | 1024x576 | 16:9 aspect ratio |
| Seed | 42 + section index | Consistent per section |

---

## Cost

| Item | Cost |
|------|------|
| SD XL (local) | $0 (electricity only) |
| ComfyUI | $0 (open source) |
| Photopea | $0 (free web app) |
| **Total per image** | **~$0.001** (electricity) |
