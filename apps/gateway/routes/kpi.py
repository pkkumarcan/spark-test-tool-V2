"""KPI monitoring routes — /api/kpi/*."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


@router.get("/dashboard")
async def get_kpi_dashboard():
    from apps.agent_runtime.kpi import get_kpi_tracker
    tracker = get_kpi_tracker()
    return tracker.get_dashboard()


@router.get("/experiments")
async def list_experiments():
    from apps.agent_runtime.kpi import get_experiment_tracker
    tracker = get_experiment_tracker()
    return {"experiments": list(tracker._experiments.values()) if hasattr(tracker, '_experiments') else []}


class ExperimentRequest(BaseModel):
    name: str = "New Experiment"
    variants: list[str] = ["A", "B"]


@router.post("/experiments")
async def create_experiment(req: ExperimentRequest):
    from apps.agent_runtime.kpi import get_experiment_tracker
    tracker = get_experiment_tracker()
    result = tracker.create_experiment(req.name, req.variants)
    return result
