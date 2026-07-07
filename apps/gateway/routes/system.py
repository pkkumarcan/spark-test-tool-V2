from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from apps.gateway.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    async def _check(name: str, url: str) -> tuple[str, str]:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                r = await client.get(url)
                return name, "online" if r.status_code == 200 or r.status_code == 404 else "error"
        except Exception:
            return name, "offline"

    results = await asyncio.gather(
        _check("ollama", f"{settings.ollama_base_url}/api/tags"),
        _check("comfyui", f"{settings.comfyui_url}/"),
    )

    services = {"gateway": "online"} | dict(results)
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "services": services,
    }


@router.get("/api/gpu/status")
async def gpu_status():
    """Returns GPU utilisation stats from nvidia-smi and Node B."""
    gpus = {}

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 7:
                    idx = int(parts[0])
                    gpus[f"gpu{idx}"] = {
                        "index": idx,
                        "name": parts[1],
                        "vram_used_mb": int(parts[2]),
                        "vram_total_mb": int(parts[3]),
                        "utilization_pct": int(parts[4]),
                        "temperature_c": int(parts[5]),
                        "power_w": float(parts[6]),
                    }
    except Exception:
        pass

    try:
        import httpx
        node_b_url = os.getenv("SPARK_NODE_B_URL", "")
        if node_b_url:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{node_b_url}/api/gpu/status", timeout=0.8)
                if r.status_code == 200:
                    remote_data = r.json()
                    for r_key, r_gpu in remote_data.get("gpus", {}).items():
                        r_gpu["name"] = f"Node B: {r_gpu.get('name', 'GPU')}"
                        gpus[f"node_b_{r_key}"] = r_gpu
    except Exception:
        pass

    return {"gpus": gpus}


OUTPUT_DIR = os.getenv("SPARK_OUTPUT_DIR", "output")


@router.get("/output/{filename:path}")
async def serve_output(filename: str):
    """Serve a file from the output directory. Protected against path traversal."""
    safe_root = os.path.realpath(OUTPUT_DIR)
    requested = os.path.realpath(os.path.join(OUTPUT_DIR, filename))
    if not requested.startswith(safe_root + os.sep) and requested != safe_root:
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(requested):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    return FileResponse(requested)
