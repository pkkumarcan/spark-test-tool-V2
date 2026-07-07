"""FLUX image generation via ComfyUI — first real media tool."""

import logging
import uuid
from typing import Any

from apps.media_workers.comfyui_client import ComfyUIClient

logger = logging.getLogger("spark.media.image")


def build_flux_workflow(
    prompt: str,
    negative_prompt: str = "blurry, low quality, distorted",
    steps: int = 8,
    width: int = 1024,
    height: int = 1024,
    model: str = "flux1-schnell-q8.gguf",
    seed: int | None = None,
) -> dict:
    """Build a ComfyUI workflow JSON for FLUX image generation."""
    if seed is None:
        seed = int(uuid.uuid4().int >> 96)

    is_flux = "flux" in model.lower()

    if is_flux:
        unet_loader_class = "UNETLoader" if model.endswith(".safetensors") else "UnetLoaderGGUF"
        unet_loader_inputs: dict[str, Any] = {"unet_name": model}
        if unet_loader_class == "UNETLoader":
            unet_loader_inputs["weight_dtype"] = "default"

        workflow = {
            "prompt": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": seed,
                        "steps": steps,
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
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": prompt, "clip": ["11", 0]},
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": negative_prompt, "clip": ["11", 0]},
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["3", 0], "vae": ["12", 0]},
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": f"spark_{uuid.uuid4().hex[:8]}",
                        "images": ["8", 0],
                    },
                },
                "10": {
                    "class_type": unet_loader_class,
                    "inputs": unet_loader_inputs,
                },
                "11": {
                    "class_type": "DualCLIPLoader",
                    "inputs": {
                        "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
                        "clip_name2": "clip_l.safetensors",
                        "type": "flux",
                    },
                },
                "12": {
                    "class_type": "VAELoader",
                    "inputs": {"vae_name": "ae.safetensors"},
                },
            }
        }
    else:
        workflow = {
            "prompt": {
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": model},
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": prompt, "clip": ["4", 1]},
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": negative_prompt, "clip": ["4", 1]},
                },
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": seed,
                        "steps": steps,
                        "cfg": 7.0,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": f"spark_{uuid.uuid4().hex[:8]}",
                        "images": ["8", 0],
                    },
                },
            }
        }

    return workflow


async def generate_image(
    client: ComfyUIClient,
    job_id: str,
    payload: dict,
) -> dict:
    """Generate an image using ComfyUI FLUX and return result dict."""
    workflow = build_flux_workflow(
        prompt=payload.get("prompt", ""),
        negative_prompt=payload.get("negative_prompt", "blurry, low quality, distorted"),
        steps=payload.get("steps", 8),
        width=payload.get("width", 1024),
        height=payload.get("height", 1024),
        model=payload.get("model", "flux1-schnell-q8.gguf"),
        seed=payload.get("seed"),
    )

    files = await client.generate_and_wait(workflow, job_id, ext="png", timeout=1800)

    return {
        "output_files": files,
        "output_url": f"/output/{job_id}.png",
    }
