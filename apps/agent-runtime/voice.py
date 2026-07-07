"""Voice agent — STT → LLM → TTS pipeline.

Transcribe audio with Whisper, process with LLM, synthesize response with F5-TTS.
"""

from __future__ import annotations

import logging
import os

import httpx

from apps.agent_runtime.llm_client import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:9000")
DEFAULT_F5_TTS_URL = os.getenv("F5_TTS_URL", "http://f5-tts:8000")


async def transcribe(audio_path: str, whisper_url: str = DEFAULT_WHISPER_URL) -> str:
    """Transcribe audio file to text using Whisper."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(audio_path, "rb") as f:
                files = {"audio_file": (os.path.basename(audio_path), f, "audio/wav")}
                r = await client.post(f"{whisper_url}/api/transcribe", files=files)
                if r.status_code == 200:
                    return r.json().get("text", "")
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
    return ""


async def synthesize(text: str, output_path: str, f5_tts_url: str = DEFAULT_F5_TTS_URL) -> bool:
    """Synthesize text to speech using F5-TTS."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{f5_tts_url}/synthesize",
                json={"text": text, "voice": "default", "speed": 1.0},
            )
            if r.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(r.content)
                return True
    except Exception as e:
        logger.error(f"F5-TTS synthesis failed: {e}")
    return False


async def voice_agent(
    audio_path: str,
    llm_client: LLMClient,
    model: str = "qwen3:8b",
    output_dir: str = "/app/output",
    whisper_url: str = DEFAULT_WHISPER_URL,
    f5_tts_url: str = DEFAULT_F5_TTS_URL,
) -> dict:
    """Full voice pipeline: transcribe → LLM → synthesize.

    Returns dict with transcript, response, and output audio path.
    """
    transcript = await transcribe(audio_path, whisper_url)
    if not transcript:
        return {"error": "Transcription failed", "transcript": ""}

    logger.info(f"Voice transcript: {transcript[:100]}...")

    response = await llm_client.chat(
        messages=[
            {"role": "system", "content": "You are Spark AI, a helpful voice assistant. Keep responses concise and conversational."},
            {"role": "user", "content": transcript},
        ],
        model=model,
    )
    response_text = response.content if hasattr(response, "content") else str(response)

    import uuid
    output_path = os.path.join(output_dir, f"voice_{uuid.uuid4().hex[:8]}.wav")
    os.makedirs(output_dir, exist_ok=True)

    syn_ok = await synthesize(response_text, output_path, f5_tts_url)

    return {
        "transcript": transcript,
        "response": response_text,
        "output_audio": output_path if syn_ok else None,
        "model": model,
    }
