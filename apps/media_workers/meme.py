"""Meme generator — LLM concept generation + ComfyUI background + Pillow text overlay."""

import json
import logging
import os

import httpx
from PIL import Image, ImageDraw, ImageFont

from apps.media_workers.comfyui_client import ComfyUIClient

logger = logging.getLogger("spark.media.meme")


def draw_impact_text(draw, text, x, y, font, outline_color="black", fill_color="white", thickness=2):
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)


def overlay_meme_text(image_path: str, top_text: str, bottom_text: str):
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        W, H = img.size

        font_size = int(H * 0.08)
        font = None
        for path in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()

        if top_text.strip():
            top_text = top_text.upper()
            try:
                bbox = draw.textbbox((0, 0), top_text, font=font)
                w = bbox[2] - bbox[0]
            except Exception:
                w = draw.textlength(top_text, font=font) if hasattr(draw, "textlength") else font_size * len(top_text) * 0.5
            x = (W - w) / 2
            y = int(H * 0.05)
            draw_impact_text(draw, top_text, x, y, font, thickness=3)

        if bottom_text.strip():
            bottom_text = bottom_text.upper()
            try:
                bbox = draw.textbbox((0, 0), bottom_text, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            except Exception:
                w = draw.textlength(bottom_text, font=font) if hasattr(draw, "textlength") else font_size * len(bottom_text) * 0.5
                h = font_size
            x = (W - w) / 2
            y = H - h - int(H * 0.08)
            draw_impact_text(draw, bottom_text, x, y, font, thickness=3)

        img.save(image_path)
        logger.info(f"Meme text overlaid: {image_path}")
    except Exception as e:
        logger.error(f"Failed to overlay meme text: {e}")


async def generate_meme(
    client: ComfyUIClient,
    job_id: str,
    payload: dict,
    output_dir: str,
    ollama_url: str = "http://localhost:11434",
) -> dict:
    topic = payload.get("prompt", "")
    image_model = payload.get("image_model", "flux1-schnell-q8.gguf")

    if not topic.strip():
        raise ValueError("Topic prompt is required")

    logger.info(f"[{job_id}] Generating meme concept via Ollama...")
    system_prompt = (
        "You are a meme designer. Based on the topic provided, generate a meme concept.\n"
        "Output exactly a JSON object with three fields:\n"
        "1. 'top_text': The text caption at the top of the meme (witty, humorous).\n"
        "2. 'bottom_text': The text caption at the bottom of the meme (punchline).\n"
        "3. 'image_prompt': A descriptive visual prompt to generate a funny background image.\n"
        "Do not write any introductory or concluding text."
    )

    ollama_payload = {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Meme Topic: {topic}"},
        ],
        "format": "json",
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client_http:
            r = await client_http.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                for preferred in ["qwen3:8b", "qwen3:14b"]:
                    if preferred in models:
                        ollama_payload["model"] = preferred
                        break
                if not any(p in models for p in ["qwen3:8b", "qwen3:14b"]) and models:
                    ollama_payload["model"] = models[0]
    except Exception:
        pass

    async with httpx.AsyncClient(timeout=60.0) as client_http:
        r = await client_http.post(f"{ollama_url}/api/chat", json=ollama_payload)
        if r.status_code != 200:
            raise RuntimeError(f"Ollama meme gen failed: {r.text}")
        content = r.json().get("message", {}).get("content", "").strip()
        meme_data = json.loads(content)

    top_text = meme_data.get("top_text", "")
    bottom_text = meme_data.get("bottom_text", "")
    img_prompt = meme_data.get("image_prompt", topic)

    logger.info(f"[{job_id}] Concept: Top: '{top_text}' | Bottom: '{bottom_text}'")

    logger.info(f"[{job_id}] Rendering background image...")
    workflow = {
        "prompt": {
            "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": image_model}},
            "11": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
                    "clip_name2": "clip_l.safetensors",
                    "type": "flux",
                },
            },
            "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": img_prompt, "clip": ["11", 0]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality", "clip": ["11", 0]}},
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 1337,
                    "steps": 4,
                    "cfg": 1.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["10", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": job_id, "images": ["8", 0]}},
        }
    }

    files = await client.generate_and_wait(workflow, job_id, ext="png", timeout=300)
    image_file = files[0] if files else os.path.join(output_dir, f"{job_id}.png")

    logger.info(f"[{job_id}] Overlaying text...")
    overlay_meme_text(image_file, top_text, bottom_text)

    return {
        "output_files": [image_file],
        "output_url": f"/output/{job_id}.png",
        "top_text": top_text,
        "bottom_text": bottom_text,
        "image_prompt": img_prompt,
    }
