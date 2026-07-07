"""F5-TTS voice synthesis."""

import asyncio
import logging
import os
import shutil

import httpx

logger = logging.getLogger("spark.media.tts")

DEFAULT_F5_TTS_URL = "http://f5-tts:8000"


async def synthesize_speech(
    job_id: str,
    payload: dict,
    output_dir: str,
    f5_tts_url: str = DEFAULT_F5_TTS_URL,
) -> dict:
    text = payload.get("text", "")
    voice = payload.get("voice", "default")
    speed = payload.get("speed", 1.0)

    if not text:
        raise ValueError("Text is required for TTS synthesis")

    output_file = os.path.join(output_dir, f"{job_id}.wav")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{f5_tts_url}/synthesize",
                json={"text": text, "voice": voice, "speed": speed},
            )

            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                if "audio" in content_type or "wav" in content_type or "octet-stream" in content_type:
                    with open(output_file, "wb") as f:
                        f.write(r.content)
                else:
                    result = r.json()
                    if "audio_path" in result:
                        audio_path = result["audio_path"]
                        if os.path.exists(audio_path):
                            shutil.copy(audio_path, output_file)
                        else:
                            raise RuntimeError(f"F5-TTS audio_path not found: {audio_path}")
                    else:
                        raise RuntimeError(f"F5-TTS returned unexpected response: {r.text[:200]}")
            else:
                raise RuntimeError(f"F5-TTS returned {r.status_code}: {r.text}")

    except httpx.RequestError as e:
        logger.warning(f"F5-TTS unreachable, creating silence fallback: {e}")
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=mono",
            "-t", str(max(len(text) * 0.05, 5)),
            output_file,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)

    return {
        "output_files": [output_file],
        "output_url": f"/output/{job_id}.wav",
    }
