"""Thumbnail generation — SD XL via ComfyUI + text overlay via FFmpeg."""

import asyncio
import logging
import os

import httpx

logger = logging.getLogger("spark.pipeline.thumbnail")

THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720


async def generate_thumbnail(
    prompt: str,
    output_path: str,
    title_text: str = "",
    comfyui_url: str = "http://localhost:8188",
) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    workflow = {
        "prompt": {
            "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-schnell-q8.gguf"}},
            "11": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
                    "clip_name2": "clip_l.safetensors",
                    "type": "flux",
                },
            },
            "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": THUMBNAIL_WIDTH, "height": THUMBNAIL_HEIGHT, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality, text", "clip": ["11", 0]}},
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 42, "steps": 4, "cfg": 1.0,
                    "sampler_name": "euler", "scheduler": "normal",
                    "denoise": 1.0, "model": ["10", 0],
                    "positive": ["6", 0], "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "thumbnail", "images": ["8", 0]}},
        }
    }

    raw_path = output_path.replace(".png", "_raw.png")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{comfyui_url}/prompt", json=workflow)
            if r.status_code == 200:
                prompt_id = r.json().get("prompt_id")
                for _ in range(60):
                    await asyncio.sleep(2)
                    hist = await client.get(f"{comfyui_url}/history/{prompt_id}")
                    if hist.status_code == 200:
                        history = hist.json()
                        if prompt_id in history:
                            outputs = history[prompt_id].get("outputs", {})
                            for _, node_output in outputs.items():
                                if "images" in node_output and node_output["images"]:
                                    fname = node_output["images"][0].get("filename")
                                    src = os.path.join(
                                        os.getenv("COMFYUI_OUTPUT_DIR", "/comfyui-output"), fname,
                                    )
                                    if os.path.exists(src):
                                        import shutil
                                        shutil.copy(src, raw_path)
                            break
    except Exception as e:
        logger.warning(f"ComfyUI thumbnail generation failed: {e}")
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"color=c=#1a1a2e:s={THUMBNAIL_WIDTH}x{THUMBNAIL_HEIGHT}:d=1",
            "-vframes", "1", raw_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)

    if title_text and os.path.exists(raw_path):
        escaped = title_text.replace("'", "'\\''").replace(":", "\\:")
        cmd = [
            "ffmpeg", "-y", "-i", raw_path,
            "-vf", (
                f"drawtext=text='{escaped}':"
                "fontcolor=white:fontsize=64:borderw=3:bordercolor=black:"
                f"x=(w-text_w)/2:y=h-text_h-40:"
                "font=DejaVu Sans"
            ),
            "-frames:v", "1", output_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)
        os.remove(raw_path)
    elif os.path.exists(raw_path):
        os.rename(raw_path, output_path)

    return output_path


async def generate_metadata(
    title: str,
    description: str,
    tags: list[str],
    channel_name: str = "",
    topic: str = "",
) -> dict:
    full_description = f"{description}\n\n"
    if channel_name:
        full_description += f"Channel: {channel_name}\n"
    if topic:
        full_description += f"Topic: {topic}\n"
    full_description += "\n[AI Content Disclosure]\nThis video was produced with AI assistance.\n\n"
    full_description += "[Sponsored / Disclosures]\nProduced by Spark AI Factory."

    return {
        "title": title[:100],
        "description": full_description,
        "tags": tags[:15],
        "category_id": "27",
        "default_language": "en",
        "status": "private",
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }
