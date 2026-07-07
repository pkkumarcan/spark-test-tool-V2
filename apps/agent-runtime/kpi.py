"""KPI dashboard data + A/B experiment tracking."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class KPITracker:
    """In-memory KPI tracker for dashboard display."""

    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._timers: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        self._experiments: dict[str, dict] = {}

    def increment(self, name: str, value: int = 1) -> None:
        self._counters[name] += value

    def record_time(self, name: str, duration_ms: float) -> None:
        self._timers[name].append(duration_ms)
        if len(self._timers[name]) > 1000:
            self._timers[name] = self._timers[name][-500:]

    def set_gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value

    def get_dashboard(self) -> dict[str, Any]:
        dashboard: dict[str, Any] = {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "timers": {},
        }
        for name, durations in self._timers.items():
            if durations:
                dashboard["timers"][name] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "p50_ms": _percentile(durations, 0.5),
                    "p95_ms": _percentile(durations, 0.95),
                    "p99_ms": _percentile(durations, 0.99),
                }
        return dashboard


class ExperimentTracker:
    """Simple A/B experiment tracker."""

    def __init__(self):
        self._experiments: dict[str, dict] = {}

    def create_experiment(
        self,
        name: str,
        variants: list[str],
        traffic_split: list[float] | None = None,
    ) -> dict:
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        if traffic_split is None:
            traffic_split = [1.0 / len(variants)] * len(variants)
        self._experiments[exp_id] = {
            "id": exp_id,
            "name": name,
            "variants": variants,
            "traffic_split": traffic_split,
            "assignments": defaultdict(list),
            "conversions": defaultdict(int),
            "created_at": time.time(),
        }
        return self._experiments[exp_id]

    def assign_variant(self, experiment_id: str, user_id: str) -> str | None:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None
        import random
        r = random.random()
        cumulative = 0.0
        for variant, split in zip(exp["variants"], exp["traffic_split"]):
            cumulative += split
            if r < cumulative:
                exp["assignments"][user_id] = variant
                return variant
        return exp["variants"][-1]

    def record_conversion(self, experiment_id: str, user_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False
        variant = exp["assignments"].get(user_id)
        if not variant:
            return False
        exp["conversions"][variant] += 1
        return True

    def get_results(self, experiment_id: str) -> dict | None:
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None
        total_users = sum(len(v) for v in exp["assignments"].values())
        results = {}
        for variant in exp["variants"]:
            assigned = len(exp["assignments"].get(variant, []))
            conversions = exp["conversions"].get(variant, 0)
            results[variant] = {
                "assigned": assigned,
                "conversions": conversions,
                "conversion_rate": conversions / assigned if assigned else 0,
            }
        return {
            "experiment_id": experiment_id,
            "name": exp["name"],
            "total_users": total_users,
            "variants": results,
        }


_kpi = KPITracker()
_experiments = ExperimentTracker()


def get_kpi_tracker() -> KPITracker:
    return _kpi


def get_experiment_tracker() -> ExperimentTracker:
    return _experiments


def _percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * pct)
    return sorted_data[min(idx, len(sorted_data) - 1)]
