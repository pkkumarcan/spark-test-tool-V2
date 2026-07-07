"""Dify workflow integration — trigger workflows and poll for results."""

from __future__ import annotations

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

DEFAULT_DIFY_URL = os.getenv("DIFY_URL", "http://localhost:5001")
DEFAULT_DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")


async def trigger_workflow(
    workflow_id: str,
    inputs: dict,
    dify_url: str = DEFAULT_DIFY_URL,
    api_key: str = DEFAULT_DIFY_API_KEY,
) -> str:
    """Trigger a Dify workflow and return the run_id."""
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{dify_url}/v1/workflows/run",
            json={"workflow_id": workflow_id, "inputs": inputs},
            headers=headers,
        )
        if r.status_code == 200:
            return r.json().get("run_id", "")
        raise RuntimeError(f"Dify trigger failed: {r.status_code} {r.text}")


async def poll_workflow(
    run_id: str,
    dify_url: str = DEFAULT_DIFY_URL,
    api_key: str = DEFAULT_DIFY_API_KEY,
    timeout: int = 300,
) -> dict:
    """Poll a Dify workflow run until completion."""
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()
    async with httpx.AsyncClient(timeout=10.0) as client:
        while time.time() - start < timeout:
            r = await client.get(
                f"{dify_url}/v1/workflows/run/{run_id}",
                headers=headers,
            )
            if r.status_code == 200:
                data = r.json()
                status = data.get("status", "")
                if status == "succeeded":
                    return {"status": "completed", "outputs": data.get("outputs", {})}
                elif status == "failed":
                    return {"status": "failed", "error": data.get("error", "Unknown error")}
            await _async_sleep(2.0)
    return {"status": "timeout", "error": f"Workflow timed out after {timeout}s"}


async def run_dify_workflow(
    workflow_id: str,
    inputs: dict,
    dify_url: str = DEFAULT_DIFY_URL,
    api_key: str = DEFAULT_DIFY_API_KEY,
) -> dict:
    """Trigger and poll a Dify workflow. Returns final result."""
    run_id = await trigger_workflow(workflow_id, inputs, dify_url, api_key)
    if not run_id:
        return {"status": "error", "error": "Failed to get run_id"}
    return await poll_workflow(run_id, dify_url, api_key)


async def _async_sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
