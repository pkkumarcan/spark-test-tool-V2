# X21 — STT (Speech-to-Text)

**Purpose:** How speech-to-text works via Whisper.  
**Estimated time:** 10 minutes

---

## Overview

Spark V2 uses OpenAI's Whisper model for speech-to-text transcription. It runs as a Docker container with GPU acceleration.

**Service:** `rhasspy/wyoming-whisper:latest`  
**Port:** 10300  
**Model:** small (configurable)

---

## Usage

### Via Media Worker
```python
from apps.media_workers.stt import transcribe_audio

result = await transcribe_audio(audio_path="/path/to/audio.wav")
# Returns: {"text": "transcribed text", "language": "en", "duration": 30.5}
```

### Via API
```bash
POST /api/audio/transcribe
{
  "audio_url": "/output/jobs/pipe_abc/voice.wav"
}
```

---

## Configuration

In `docker-compose.yml`:
```yaml
whisper:
  image: rhasspy/wyoming-whisper:latest
  ports:
    - "10300:10300"
  command: --model small --language en
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

**Available models:** tiny, base, small, medium, large  
**Larger models = better accuracy but more VRAM and slower**

---

## Use Cases in Pipeline

- **Voiceover QC:** Verify synthesized audio matches expected text
- **Content extraction:** Extract audio from uploaded videos for re-processing
- **Accessibility:** Generate subtitles from video content
