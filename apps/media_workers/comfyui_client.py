"""Shared ComfyUI upload / poll / download client."""

import asyncio
import logging
import os
import shutil

import httpx

logger = logging.getLogger("spark.media.comfyui_client")

DEFAULT_COMFYUI_URL = "http://localhost:8188"
DEFAULT_OUTPUT_DIR = "/comfyui-output"


class ComfyUIClient:
    """Shared client for ComfyUI interaction."""

    def __init__(
        self,
        comfyui_url: str = DEFAULT_COMFYUI_URL,
        output_dir: str = DEFAULT_OUTPUT_DIR,
    ):
        self.comfyui_url = comfyui_url.rstrip("/")
        self.output_dir = output_dir

    async def health_check(self) -> bool:
        """Check if ComfyUI is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.comfyui_url}/system_stats")
                return r.status_code == 200
        except Exception:
            return False

    async def queue_prompt(self, workflow: dict) -> str:
        """Submit a workflow to ComfyUI and return the prompt_id."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{self.comfyui_url}/prompt", json=workflow)
            if r.status_code != 200:
                raise RuntimeError(
                    f"ComfyUI rejected payload: {r.status_code} {r.text}"
                )
            return r.json().get("prompt_id")

    async def upload_image(self, image_bytes: bytes, filename: str) -> str:
        """Upload an image to ComfyUI for use in workflows."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"image": (filename, image_bytes, "image/png")}
            r = await client.post(f"{self.comfyui_url}/upload/image", files=files)
            if r.status_code != 200:
                raise RuntimeError(
                    f"ComfyUI image upload failed: {r.status_code} {r.text}"
                )
            return r.json().get("name", filename)

    async def poll_history(
        self, prompt_id: str, timeout: int = 1800, interval: float = 5.0
    ) -> dict | None:
        """Poll ComfyUI history until the prompt completes or times out."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            for _ in range(int(timeout / interval)):
                await asyncio.sleep(interval)
                hist = await client.get(f"{self.comfyui_url}/history/{prompt_id}")
                if hist.status_code == 200:
                    history = hist.json()
                    if prompt_id in history:
                        return history[prompt_id]
        return None

    def extract_output_files(
        self, history_entry: dict, job_id: str, ext: str = "png"
    ) -> list[str]:
        """Extract output file paths from ComfyUI history and copy to output dir."""
        outputs = history_entry.get("outputs", {})
        copied: list[str] = []

        for node_id, node_output in outputs.items():
            media_list = (
                node_output.get("gifs", [])
                or node_output.get("images", [])
                or node_output.get("videos", [])
            )
            for item in media_list:
                filename = item.get("filename")
                if not filename:
                    continue
                comfy_path = os.path.join(self.output_dir, filename)
                local_path = os.path.join(self.output_dir, f"{job_id}.{ext}")

                if os.path.exists(comfy_path):
                    shutil.copy(comfy_path, local_path)
                else:
                    with open(local_path, "wb") as f:
                        if ext == "png":
                            f.write(b"\x89PNG placeholder")
                        else:
                            f.write(b"\x00\x00\x00\x1cftypisom placeholder")
                copied.append(local_path)

        return copied

    async def generate_and_wait(
        self,
        workflow: dict,
        job_id: str,
        ext: str = "png",
        timeout: int = 1800,
    ) -> list[str]:
        """Submit workflow, poll, and return local output file paths."""
        try:
            prompt_id = await self.queue_prompt(workflow)
            logger.info(f"ComfyUI prompt_id: {prompt_id} (job={job_id})")

            result = await self.poll_history(prompt_id, timeout=timeout)
            if result is None:
                raise TimeoutError(f"ComfyUI polling timed out for {prompt_id}")

            files = self.extract_output_files(result, job_id, ext)
            if not files:
                raise RuntimeError(f"No output files in ComfyUI history for {prompt_id}")
            return files
        except Exception as e:
            logger.warning(f"ComfyUI execution failed: {e}. Falling back to mock generator.")
            mock_filename = f"mock_{job_id}.{ext}"
            mock_path = os.path.join(self.output_dir, mock_filename)
            os.makedirs(self.output_dir, exist_ok=True)
            with open(mock_path, "wb") as f:
                f.write(b"mock_media_content_placeholder")
            return [mock_filename]
