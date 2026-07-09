# X107 — Voice Agent

**Purpose:** STT → LLM → TTS voice pipeline for conversational voice interaction.  
**Created:** 2026-07-09 (V3 — V2 agent integration docs)  
**Estimated time:** 10 minutes

---

## Overview

The voice agent provides a complete voice-to-voice pipeline:
1. **STT:** Transcribe user audio to text (Whisper)
2. **LLM:** Generate response text (Ollama)
3. **TTS:** Synthesize response audio (F5-TTS)

---

## Pipeline Flow

```
Audio Input → Whisper (STT) → Text → LLM (Ollama) → Response Text → F5-TTS (TTS) → Audio Output
```

### Step-by-Step

1. User speaks into microphone
2. Audio file sent to Whisper for transcription
3. Transcript sent to LLM for response generation
4. Response text sent to F5-TTS for voice synthesis
5. Audio file returned to user

---

## Architecture

```python
async def voice_agent(audio_path, llm_client, model, output_dir):
    # 1. Transcribe audio
    transcript = await transcribe(audio_path)
    if not transcript:
        return {"error": "Transcription failed"}

    # 2. Generate LLM response
    response = await llm_client.chat(
        messages=[
            {"role": "system", "content": "You are Spark AI, a helpful voice assistant."},
            {"role": "user", "content": transcript},
        ],
        model=model,
    )

    # 3. Synthesize speech
    output_path = f"{output_dir}/voice_{uuid}.wav"
    await synthesize(response.content, output_path)

    return {
        "transcript": transcript,
        "response": response.content,
        "output_audio": output_path,
    }
```

---

## Components

### 1. Speech-to-Text (Whisper)

**Service:** `rhasspy/wyoming-whisper:latest`  
**Port:** 10300  
**Model:** small

```python
async def transcribe(audio_path, whisper_url):
    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(audio_path, "rb") as f:
            files = {"audio_file": ("audio.wav", f, "audio/wav")}
            r = await client.post(f"{whisper_url}/api/transcribe", files=files)
            return r.json().get("text", "")
```

### 2. LLM Processing (Ollama)

**Service:** Ollama on host  
**Default model:** qwen3:8b

```python
response = await llm_client.chat(
    messages=[
        {"role": "system", "content": "You are Spark AI, a helpful voice assistant. Keep responses concise and conversational."},
        {"role": "user", "content": transcript},
    ],
    model="qwen3:8b",
)
```

### 3. Text-to-Speech (F5-TTS)

**Service:** `climatologist/f5-tts:latest`  
**Port:** 9880  
**VRAM:** ~4 GB

```python
async def synthesize(text, output_path, f5_tts_url):
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{f5_tts_url}/synthesize",
            json={"text": text, "voice": "default", "speed": 1.0},
        )
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True
    return False
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/voice/transcribe` | POST | Transcribe audio to text |
| `/api/voice/synthesize` | POST | Synthesize text to audio |
| `/api/voice/agent` | POST | Full voice pipeline |

---

## Usage Examples

### Full Voice Pipeline
```bash
POST /api/voice/agent
Content-Type: multipart/form-data
audio: <audio-file.wav>

Response:
{
  "transcript": "What's the weather today?",
  "response": "I don't have access to weather data, but I can help with other questions.",
  "output_audio": "/output/voice_abc12345.wav"
}
```

### Transcribe Only
```bash
POST /api/voice/transcribe
Content-Type: multipart/form-data
audio: <audio-file.wav>

Response:
{
  "text": "What's the weather today?"
}
```

### Synthesize Only
```bash
POST /api/voice/synthesize
{
  "text": "Hello, how can I help you?",
  "voice": "default"
}

Response:
<binary audio data>
```

---

## Configuration

### Environment Variables

```bash
# Whisper
WHISPER_URL=http://whisper:9000

# F5-TTS
F5_TTS_URL=http://f5-tts:8000

# LLM
SPARK_OLLAMA_BASE_URL=http://localhost:11434
SPARK_DEFAULT_MODEL=qwen3:8b
```

---

## Voice Customization

### F5-TTS Voices
- `default` — Standard voice
- Custom voices can be added via voice cloning

### ElevenLabs Integration
For higher quality voice output, replace F5-TTS with ElevenLabs:

```python
async def synthesize_elevenlabs(text, output_path, api_key, voice_id):
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key},
            json={"text": text, "model_id": "eleven_monolingual_v1"},
        )
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True
    return False
```

---

## Limitations

- **Latency:** Full pipeline takes 5-15 seconds
- **Whisper accuracy:** Depends on audio quality and accent
- **F5-TTS quality:** Good but not as natural as ElevenLabs
- **No real-time:** Batch processing only (not streaming)
- **Language:** English only (Whisper supports multilingual)
