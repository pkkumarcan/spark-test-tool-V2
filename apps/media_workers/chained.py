"""Chained generator — story → images → audio content pipeline."""

from __future__ import annotations

import json
import logging

import httpx

from apps.agent_runtime.llm_client import LLMClient

logger = logging.getLogger(__name__)


async def generate_story(
    llm_client: LLMClient,
    topic: str,
    model: str = "qwen3:8b",
    num_sections: int = 4,
) -> dict:
    """Generate a story with sections for visual/audio generation."""
    system_prompt = (
        f"You are a creative storyteller. Generate a {num_sections}-section story about the topic.\n"
        "Output a JSON object with:\n"
        "- title: story title\n"
        "- sections: list of objects with: narration (text), image_prompt (visual description), duration_seconds (number)\n"
        "Return ONLY the JSON."
    )

    try:
        resp = await llm_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Topic: {topic}"},
            ],
            model=model,
            temperature=0.8,
        )
        raw = resp.content if hasattr(resp, "content") else str(resp)
        story = json.loads(_clean_json(raw))
    except Exception as e:
        logger.warning(f"Story generation failed: {e}")
        story = {
            "title": f"Story about {topic}",
            "sections": [
                {"narration": f"Section {i+1} about {topic}.", "image_prompt": f"Visual for {topic} section {i+1}", "duration_seconds": 15}
                for i in range(num_sections)
            ],
        }

    return story


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return text[start:end]
    return text


async def generate_images_for_sections(
    story: dict,
    comfyui_url: str = "http://localhost:8188",
    output_dir: str = "/app/output",
) -> dict:
    """Generate images for each story section via ComfyUI."""
    sections = story.get("sections", [])
    image_paths = {}

    for i, sec in enumerate(sections):
        prompt = sec.get("image_prompt", story.get("title", ""))
        workflow = {
            "prompt": {
                "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-schnell-q8.gguf"}},
                "11": {
                    "class_type": "DualCLIPLoader",
                    "inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"},
                },
                "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
                "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 576, "batch_size": 1}},
                "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
                "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality", "clip": ["11", 0]}},
                "3": {"class_type": "KSampler", "inputs": {"seed": 42 + i, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
                "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
                "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"chain_{i}", "images": ["8", 0]}},
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{comfyui_url}/prompt", json=workflow)
                if r.status_code == 200:
                    image_paths[f"section_{i}"] = f"/output/chain_{i}.png"
        except Exception as e:
            logger.warning(f"Image gen failed for section {i}: {e}")
            image_paths[f"section_{i}"] = None

    return image_paths


async def chain_generate(
    topic: str,
    llm_client: LLMClient,
    comfyui_url: str = "http://localhost:8188",
    output_dir: str = "/app/output",
    model: str = "qwen3:8b",
) -> dict:
    """Full chain: story → images → return combined result."""
    story = await generate_story(llm_client, topic, model)
    images = await generate_images_for_sections(story, comfyui_url, output_dir)

    return {
        "title": story.get("title", topic),
        "sections": story.get("sections", []),
        "images": images,
        "section_count": len(story.get("sections", [])),
    }
