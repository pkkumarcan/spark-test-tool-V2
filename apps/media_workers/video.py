"""ComfyUI video generation — LTX, Wan, CogVideoX, Mochi."""

import base64
import logging
import os
import uuid

from apps.media_workers.comfyui_client import ComfyUIClient

logger = logging.getLogger("spark.media.video")

SUPPORTED_VIDEO_MODELS = [
    "ltx-2.3-22b-dev-Q4_K_M.gguf",
    "wan2.2_14b_q4.gguf",
    "cogvideox_5b_i2v_bf16.safetensors",
    "mochi_preview_fp8.safetensors",
    "allegro_v1_0_fp8.safetensors",
    "dreamshaper_8.safetensors",
]


def _build_ltx_workflow(
    prompt: str,
    negative_prompt: str,
    steps: int,
    width: int,
    height: int,
    frames: int,
    seed: int,
    cfg: float,
    model: str,
    vae_tiling: bool,
    start_filename: str = "",
    end_filename: str = "",
) -> dict:
    workflow = {
        "prompt": {
            "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": model}},
            "11": {
                "class_type": "DualCLIPLoaderGGUF",
                "inputs": {
                    "clip_name1": "gemma-3-12b-it-UD-Q4_K_XL.gguf",
                    "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                    "type": "ltxv",
                },
            },
            "12": {
                "class_type": "VAELoader",
                "inputs": {"vae_name": "LTX23_video_vae_bf16.safetensors"},
            },
            "5": {
                "class_type": "EmptyLTXVLatentVideo",
                "inputs": {"width": width, "height": height, "length": frames, "batch_size": 1},
            },
            "32": {
                "class_type": "LTXVAudioVAELoader",
                "inputs": {"ckpt_name": "LTX23_audio_vae_bf16.safetensors"},
            },
            "34": {
                "class_type": "LTXVEmptyLatentAudio",
                "inputs": {
                    "frames_number": frames,
                    "frame_rate": 25,
                    "batch_size": 1,
                    "audio_vae": ["32", 0],
                },
            },
            "35": {
                "class_type": "LTXVConcatAVLatent",
                "inputs": {"video_latent": ["5", 0], "audio_latent": ["34", 0]},
            },
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["11", 0]},
            },
            "8": {
                "class_type": "LTXVConditioning",
                "inputs": {"positive": ["6", 0], "negative": ["7", 0], "frame_rate": 25.0},
            },
            "9": {
                "class_type": "LTXVScheduler",
                "inputs": {
                    "steps": steps,
                    "max_shift": 2.05,
                    "base_shift": 0.95,
                    "stretch": True,
                    "terminal": 0.1,
                },
            },
            "15": {
                "class_type": "CFGGuider",
                "inputs": {
                    "model": ["10", 0],
                    "positive": ["8", 0],
                    "negative": ["8", 1],
                    "cfg": cfg,
                },
            },
            "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
            "20": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
            "21": {
                "class_type": "SamplerCustomAdvanced",
                "inputs": {
                    "noise": ["20", 0],
                    "guider": ["15", 0],
                    "sampler": ["16", 0],
                    "sigmas": ["9", 0],
                    "latent_image": ["35", 0],
                },
            },
            "36": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["21", 0]}},
            "22": {
                "class_type": "VAEDecodeTiled" if vae_tiling else "VAEDecode",
                "inputs": {
                    "samples": ["36", 0],
                    "vae": ["12", 0],
                    **(
                        {"tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}
                        if vae_tiling
                        else {}
                    ),
                },
            },
            "33": {
                "class_type": "LTXVAudioVAEDecode",
                "inputs": {"samples": ["36", 1], "audio_vae": ["32", 0]},
            },
            "23": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["22", 0],
                    "audio": ["33", 0],
                    "frame_rate": 25.0,
                    "loop_count": 0,
                    "filename_prefix": f"spark_{uuid.uuid4().hex[:8]}",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
        }
    }

    if start_filename:
        workflow["prompt"]["37"] = {"class_type": "LoadImage", "inputs": {"image": start_filename}}
        guide_node = {
            "class_type": "LTXVAddGuide",
            "inputs": {
                "positive": ["8", 0],
                "negative": ["8", 1],
                "vae": ["12", 0],
                "latent": ["35", 0],
                "image": ["37", 0],
                "frame_idx": 0,
                "strength": 1.0,
            },
        }
        if end_filename:
            workflow["prompt"]["39"] = {
                "class_type": "LoadImage",
                "inputs": {"image": end_filename},
            }
            workflow["prompt"]["40"] = {
                "class_type": "LTXVAddGuide",
                "inputs": {
                    "positive": ["38", 0],
                    "negative": ["38", 1],
                    "vae": ["12", 0],
                    "latent": ["38", 2],
                    "image": ["39", 0],
                    "frame_idx": -1,
                    "strength": 1.0,
                },
            }
        workflow["prompt"]["38"] = guide_node
        workflow["prompt"]["15"]["inputs"]["positive"] = ["38", 0]
        workflow["prompt"]["15"]["inputs"]["negative"] = ["38", 1]
        workflow["prompt"]["21"]["inputs"]["latent_image"] = ["38", 2]

    return workflow


def _build_wan_workflow(
    prompt: str,
    negative_prompt: str,
    steps: int,
    width: int,
    height: int,
    frames: int,
    seed: int,
    cfg: float,
    model: str,
    vae_tiling: bool,
    start_filename: str = "",
    end_filename: str = "",
) -> dict:
    decoder_inputs = {
        "samples": ["3", 0],
        "vae": ["12", 0],
        **(
            {"tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}
            if vae_tiling
            else {}
        ),
    }

    workflow = {
        "prompt": {
            "30": {
                "class_type": "ModelComputeDtype",
                "inputs": {"model": ["10", 0], "dtype": "bf16"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "uni_pc",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["30", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": width, "height": height, "batch_size": frames},
            },
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["11", 0]},
            },
            "8": {
                "class_type": "VAEDecodeTiled" if vae_tiling else "VAEDecode",
                "inputs": decoder_inputs,
            },
            "9": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["8", 0],
                    "frame_rate": 16.0,
                    "loop_count": 0,
                    "filename_prefix": f"spark_{uuid.uuid4().hex[:8]}",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
            "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": model}},
            "11": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": "umt5_xxl_fp8.safetensors",
                    "clip_name2": "clip_l.safetensors",
                    "type": "hunyuan_video",
                },
            },
            "12": {"class_type": "VAELoader", "inputs": {"vae_name": "wan2.2_vae.safetensors"}},
        }
    }

    if start_filename and not end_filename:
        workflow["prompt"]["13"] = {"class_type": "LoadImage", "inputs": {"image": start_filename}}
        workflow["prompt"]["14"] = {
            "class_type": "WanImageToVideo",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["12", 0],
                "width": width,
                "height": height,
                "length": frames,
                "batch_size": 1,
                "start_image": ["13", 0],
            },
        }
        workflow["prompt"]["3"]["inputs"]["positive"] = ["14", 0]
        workflow["prompt"]["3"]["inputs"]["negative"] = ["14", 1]
        workflow["prompt"]["3"]["inputs"]["latent_image"] = ["14", 2]

    elif start_filename and end_filename:
        workflow["prompt"]["13"] = {"class_type": "LoadImage", "inputs": {"image": start_filename}}
        workflow["prompt"]["14"] = {"class_type": "LoadImage", "inputs": {"image": end_filename}}
        workflow["prompt"]["15"] = {
            "class_type": "WanFirstLastFrameToVideo",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "vae": ["12", 0],
                "width": width,
                "height": height,
                "length": frames,
                "batch_size": 1,
                "start_image": ["13", 0],
                "end_image": ["14", 0],
            },
        }
        workflow["prompt"]["3"]["inputs"]["positive"] = ["15", 0]
        workflow["prompt"]["3"]["inputs"]["negative"] = ["15", 1]
        workflow["prompt"]["3"]["inputs"]["latent_image"] = ["15", 2]

    return workflow


def _build_cogvideox_workflow(
    prompt: str,
    negative_prompt: str,
    steps: int,
    width: int,
    height: int,
    frames: int,
    seed: int,
    cfg: float,
    model_name: str,
    vae_tiling: bool,
    start_filename: str = "",
    end_filename: str = "",
) -> dict:
    model_loader = {
        "class_type": "CogVideoXModelLoader",
        "inputs": {
            "model": model_name,
            "base_precision": "bf16",
            "quantization": "disabled",
            "load_device": "main_device",
            "enable_sequential_cpu_offload": False,
        },
    }
    clip_loader = {
        "class_type": "CLIPLoader",
        "inputs": {"clip_name": "t5xxl_fp8_e4m3fn.safetensors", "type": "sd3"},
    }
    vae_loader = {
        "class_type": "CogVideoXVAELoader",
        "inputs": {"model_name": "cogvideox_vae_bf16.safetensors", "precision": "bf16"},
    }
    empty_latent = {
        "class_type": "EmptyLatentImage",
        "inputs": {"width": width, "height": height, "batch_size": frames},
    }
    pos_encode = {
        "class_type": "CogVideoTextEncode",
        "inputs": {"clip": ["1", 0], "prompt": prompt},
    }
    neg_encode = {
        "class_type": "CogVideoTextEncode",
        "inputs": {"clip": ["1", 0], "prompt": negative_prompt},
    }
    sampler = {
        "class_type": "CogVideoSampler",
        "inputs": {
            "model": ["0", 0],
            "positive": ["4", 0],
            "negative": ["5", 0],
            "samples": ["3", 0],
            "num_frames": frames,
            "steps": steps,
            "cfg": cfg,
            "seed": seed,
            "scheduler": "CogVideoXDDIM",
        },
    }

    additional_nodes: dict = {}
    if start_filename:
        additional_nodes["13"] = {"class_type": "LoadImage", "inputs": {"image": start_filename}}
        image_encode_inputs = {"vae": ["2", 0], "start_image": ["13", 0], "enable_tiling": vae_tiling}
        if end_filename:
            additional_nodes["14"] = {"class_type": "LoadImage", "inputs": {"image": end_filename}}
            image_encode_inputs["end_image"] = ["14", 0]
        additional_nodes["15"] = {"class_type": "CogVideoImageEncode", "inputs": image_encode_inputs}
        sampler["inputs"]["image_cond_latents"] = ["15", 0]

    decode = {
        "class_type": "CogVideoDecode",
        "inputs": {
            "vae": ["2", 0],
            "samples": ["6", 0],
            "enable_vae_tiling": vae_tiling,
            "tile_sample_min_height": 240,
            "tile_sample_min_width": 360,
            "tile_overlap_factor_height": 0.2,
            "tile_overlap_factor_width": 0.2,
            "auto_tile_size": True,
        },
    }
    combine = {
        "class_type": "VHS_VideoCombine",
        "inputs": {
            "images": ["7", 0],
            "frame_rate": 25.0,
            "filename_prefix": f"spark_{uuid.uuid4().hex[:8]}",
            "format": "video/h264-mp4",
            "pingpong": False,
            "loop_count": 0,
            "save_output": True,
        },
    }

    return {
        "prompt": {
            "0": model_loader,
            "1": clip_loader,
            "2": vae_loader,
            "3": empty_latent,
            "4": pos_encode,
            "5": neg_encode,
            "6": sampler,
            "7": decode,
            "8": combine,
            **additional_nodes,
        }
    }


def _build_mochi_workflow(
    prompt: str,
    negative_prompt: str,
    steps: int,
    width: int,
    height: int,
    frames: int,
    seed: int,
    cfg: float,
    model: str,
    vae_tiling: bool,
) -> dict:
    return {
        "prompt": {
            "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": model}},
            "11": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
                    "clip_name2": "clip_l.safetensors",
                    "type": "hunyuan_video",
                },
            },
            "12": {"class_type": "VAELoader", "inputs": {"vae_name": "wan2.2_vae.safetensors"}},
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "uni_pc",
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
                "inputs": {"width": width, "height": height, "batch_size": frames},
            },
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["11", 0]}},
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["11", 0]},
            },
            "8": {
                "class_type": "VAEDecodeTiled" if vae_tiling else "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["12", 0],
                    **(
                        {"tile_size": 512, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}
                        if vae_tiling
                        else {}
                    ),
                },
            },
            "9": {
                "class_type": "VHS_VideoCombine",
                "inputs": {
                    "images": ["8", 0],
                    "frame_rate": 16.0,
                    "loop_count": 0,
                    "filename_prefix": f"spark_{uuid.uuid4().hex[:8]}",
                    "format": "video/h264-mp4",
                    "pingpong": False,
                    "save_output": True,
                },
            },
        }
    }


async def upload_image_to_comfyui(client: ComfyUIClient, image_data: str) -> str:
    if not image_data:
        return ""
    if image_data.startswith("data:image/"):
        _, encoded = image_data.split(",", 1)
        file_bytes = base64.b64decode(encoded)
    elif image_data.startswith("/output/"):
        local_path = os.path.join(client.output_dir, image_data.replace("/output/", ""))
        with open(local_path, "rb") as f:
            file_bytes = f.read()
    else:
        file_bytes = base64.b64decode(image_data)
    filename = f"upload_{uuid.uuid4().hex[:8]}.png"
    return await client.upload_image(file_bytes, filename)


async def generate_video(
    client: ComfyUIClient,
    job_id: str,
    payload: dict,
) -> dict:
    prompt = payload.get("prompt", "")
    negative_prompt = payload.get("negative_prompt", "blurry, low quality, distorted")
    steps = payload.get("steps", 20)
    width = payload.get("width", 480)
    height = payload.get("height", 320)
    frames = payload.get("frames", 49)
    model = payload.get("model", "wan2.2_14b_q4.gguf")
    seed = payload.get("seed", int(uuid.uuid4().int >> 96))
    cfg = payload.get("cfg", 1.0 if "ltx" in model.lower() else 6.0)
    mode = payload.get("mode", "t2v")
    start_image = payload.get("start_image", "")
    end_image = payload.get("end_image", "")
    vae_tiling = payload.get("vae_tiling", False)

    if "wan" in model.lower():
        vae_tiling = True

    start_filename = ""
    end_filename = ""
    if mode in ("i2v", "interpolation") and start_image:
        start_filename = await upload_image_to_comfyui(client, start_image)
    if mode == "interpolation" and end_image:
        end_filename = await upload_image_to_comfyui(client, end_image)

    if "ltx" in model.lower():
        workflow = _build_ltx_workflow(
            prompt, negative_prompt, steps, width, height, frames, seed, cfg, model, vae_tiling,
            start_filename, end_filename,
        )
    elif model.lower().startswith("cogvideox"):
        workflow = _build_cogvideox_workflow(
            prompt, negative_prompt, steps, width, height, frames, seed, cfg, model, vae_tiling,
            start_filename, end_filename,
        )
    elif "mochi" in model.lower():
        workflow = _build_mochi_workflow(
            prompt, negative_prompt, steps, width, height, frames, seed, cfg, model, vae_tiling,
        )
    else:
        workflow = _build_wan_workflow(
            prompt, negative_prompt, steps, width, height, frames, seed, cfg, model, vae_tiling,
            start_filename, end_filename,
        )

    files = await client.generate_and_wait(workflow, job_id, ext="mp4", timeout=1800)

    return {
        "output_files": files,
        "output_url": f"/output/{job_id}.mp4",
    }
