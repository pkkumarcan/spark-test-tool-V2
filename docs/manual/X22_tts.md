# X22 — TTS (Text-to-Speech)

**Purpose:** Voice synthesis for pipeline narration — ElevenLabs (primary) and F5-TTS (fallback).  
**Updated:** 2026-07-09 (V3 — ElevenLabs as primary per vidIQ recommendation)  
**Estimated time:** 10 minutes

---

## Overview

Spark V2 uses two TTS systems:
1. **ElevenLabs** (primary) — Cloud-based, high-quality, $5/mo
2. **F5-TTS** (fallback) — Local on GPU, free, lower quality

---

## ElevenLabs (Primary)

**Service:** ElevenLabs API  
**Cost:** $5/mo (Starter plan)  
**Quality:** Industry-leading natural voices

### Setup
1. Sign up at https://elevenlabs.io
2. Get API key from profile settings
3. Add to `.env`:
```bash
ELEVENLABS_API_KEY=your-key-here
```

### Usage
```python
from apps.media_workers.tts import synthesize_speech

wav_path = await synthesize_speech(
    text="Welcome to Macro Lens. Today we explore central bank policy.",
    voice_id="George",  # or "Daniel", "Adam", etc.
    model_id="eleven_monolingual_v1",
    output_path="/path/to/output.mp3"
)
```

### Voice Assignments per Channel

| Channel | Voice Style | ElevenLabs Voice | Notes |
|---------|-------------|------------------|-------|
| DFW | None | — | Music only, no voiceover |
| STM | Deep, measured male | "George" or "Daniel" | Stoic, authoritative |
| ODA | Tense storytelling | "Adam" or "Josh" | Suspenseful |
| PKP | Confident, knowledgeable | Custom clone | Health expert tone |
| DKS | Low, measured, ominous | "Liam" | Dark psychology |
| GDB | Authoritative, measured | "Brian" or "Antoni" | News briefing |
| ISL | Warm, calm, resonant | "Freya" or "Patrick" | Spiritual |
| NHZ | Wonder-driven | Custom clone | Science explorer |
| RMR | Conversational, practical | Custom clone | Travel guide |
| BWA | Tutorial-friendly | Custom clone | Developer |

### ElevenLabs API Call
```python
import httpx

async def elevenlabs_tts(text: str, voice_id: str, api_key: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key},
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                }
            }
        )
        resp.raise_for_status()
        return resp.content
```

---

## F5-TTS (Fallback)

**Service:** `climatologist/f5-tts:latest` Docker container  
**Cost:** Free (runs locally on GPU)  
**VRAM:** ~4 GB  
**Port:** 9880

### When to Use
- ElevenLabs is down or rate-limited
- Generating large batches of voiceover
- Testing without API costs

### Usage
```python
async with httpx.AsyncClient(timeout=120.0) as client:
    r = await client.post(
        "http://localhost:9880/synthesize",
        json={"text": narration, "voice": "default", "speed": 1.0},
    )
    if r.status_code == 200:
        with open(wav_path, "wb") as f:
            f.write(r.content)
```

### Fallback to Silence
If both TTS systems are down, generate silent audio:
```bash
ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 15 output.wav
```

---

## Pipeline Integration

### Voiceover Stage Flow
```
Script sections → For each section:
  1. Try ElevenLabs API → MP3 file
  2. If fails → Try F5-TTS → WAV file
  3. If fails → Generate silence via FFmpeg
```

### Output Structure
```
output/jobs/pipe_abc12345/
├── audio/
│   └── voice/
│       ├── S01.mp3    # HOOK narration
│       ├── S02.mp3    # INTRO narration
│       ├── S03.mp3    # BODY narration
│       └── S04.mp3    # CTA narration
```

---

## Quality Tips

- **Stability setting:** 0.5 for natural variation, 0.8 for consistent delivery
- **Similarity boost:** 0.75 for most channels, 0.6 for more variation
- **Speed:** 1.0 for normal, 0.9 for slightly slower (philosophical content)
- **Break long scripts** into sections (max 500 chars per ElevenLabs call)

---

## Cost Tracking

| System | Cost per Video | Monthly (20 videos) |
|--------|---------------|---------------------|
| ElevenLabs | ~$0.10 | ~$2 |
| F5-TTS | $0 (electricity) | ~$0.50 |
| **Total TTS** | **~$0.10** | **~$2.50** |
