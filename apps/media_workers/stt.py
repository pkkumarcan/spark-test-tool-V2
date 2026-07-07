"""Whisper ASR transcription."""

import logging
import os
import tempfile
import uuid

import httpx

logger = logging.getLogger("spark.media.stt")

DEFAULT_WHISPER_URL = "http://whisper:9000"


async def transcribe_audio(
    job_id: str,
    payload: dict,
    output_dir: str,
    whisper_url: str = DEFAULT_WHISPER_URL,
) -> dict:
    """Transcribe audio using Whisper service.

    payload should contain:
      - audio_path: path to audio file on disk
      - language: optional language code (default "en")
    """
    audio_path = payload.get("audio_path", "")
    language = payload.get("language", "en")

    if not audio_path or not os.path.exists(audio_path):
        raise ValueError(f"Audio file not found: {audio_path}")

    ext = os.path.splitext(audio_path)[1] or ".wav"
    temp_path = os.path.join(tempfile.gettempdir(), f"whisper_{uuid.uuid4().hex}{ext}")

    try:
        import shutil
        shutil.copy(audio_path, temp_path)

        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(temp_path, "rb") as f:
                files = {"audio_file": (os.path.basename(audio_path), f, "audio/wav")}
                params = {"task": "transcribe", "output": "json", "vad_filter": "true"}
                if language:
                    params["language"] = language

                r = await client.post(f"{whisper_url}/asr", files=files, params=params)

                if r.status_code == 200:
                    result = r.json()
                else:
                    raise RuntimeError(f"Whisper returned {r.status_code}: {r.text}")

        text = result.get("text", "")
        output_file = os.path.join(output_dir, f"{job_id}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        return {
            "output_files": [output_file],
            "output_url": f"/output/{job_id}.txt",
            "text": text,
            "segments": result.get("segments", []),
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
