"""Metrics routes — /api/metrics/*."""

from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])


@router.get("/api/metrics/summary")
async def metrics_summary():
    """Aggregate metrics from all completed sessions."""
    sessions_dir = os.getenv("SPARK_SESSIONS_DIR", "/workspace/.spark_coder/sessions")
    if not os.path.exists(sessions_dir):
        return {"sessions": 0, "avg_tokens": 0, "avg_time_s": 0, "tool_usage": {}}

    total_tokens = 0
    total_time = 0.0
    tool_usage = {}
    session_count = 0

    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(sessions_dir, fname), encoding="utf-8") as f:
                data = json.load(f)
            metrics = data.get("meta", {}).get("metrics", {})
            if not metrics:
                continue
            session_count += 1
            total_tokens += metrics.get("total_tokens", 0)
            total_time += metrics.get("total_time_s", 0)
            for t in metrics.get("tools_used", []):
                tool_usage[t] = tool_usage.get(t, 0) + 1
        except Exception:
            continue

    return {
        "sessions": session_count,
        "avg_tokens": total_tokens // max(session_count, 1),
        "avg_time_s": round(total_time / max(session_count, 1), 2),
        "total_tokens": total_tokens,
        "total_time_s": round(total_time, 2),
        "tool_usage": tool_usage,
    }
