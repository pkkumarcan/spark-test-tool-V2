"""Golden trajectory replay framework.

Load a trajectory JSON, execute the agent against the prompt,
and diff the resulting tool-call sequence against the expected golden baseline.

Usage:
    python -m tests.golden_trajectories.replay trajectory_001.json
    pytest tests/golden_trajectories/ -v
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

TRAJECTORIES_DIR = Path(__file__).parent


@dataclass
class ToolCallDiff:
    tool_name: str
    expected_args: dict[str, Any]
    actual_args: dict[str, Any]
    match: bool
    reason: str = ""


@dataclass
class TrajectoryResult:
    trajectory_id: str
    prompt: str
    tool_calls_made: list[dict[str, Any]]
    tool_call_diffs: list[ToolCallDiff] = field(default_factory=list)
    states_visited: list[str] = field(default_factory=list)
    completed: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.completed
            and all(d.match for d in self.tool_call_diffs)
            and len(self.errors) == 0
        )

    def summary(self) -> str:
        lines = [f"Trajectory: {self.trajectory_id}"]
        lines.append(f"  Prompt: {self.prompt}")
        lines.append(f"  Completed: {self.completed}")
        lines.append(f"  Tool calls made: {len(self.tool_calls_made)}")
        lines.append(f"  Diffs: {len(self.tool_call_diffs)}")
        mismatches = [d for d in self.tool_call_diffs if not d.match]
        if mismatches:
            lines.append("  MISMATCHES:")
            for d in mismatches:
                lines.append(f"    - {d.tool_name}: {d.reason}")
        if self.errors:
            lines.append("  ERRORS:")
            for e in self.errors:
                lines.append(f"    - {e}")
        lines.append(f"  RESULT: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


def load_trajectory(path: str | Path) -> dict:
    """Load a trajectory JSON file."""
    with open(path) as f:
        return json.load(f)


def load_all_trajectories() -> list[dict]:
    """Load all trajectory_*.json files from the golden_trajectories directory."""
    trajectories = []
    for p in sorted(TRAJECTORIES_DIR.glob("trajectory_*.json")):
        trajectories.append(load_trajectory(p))
    return trajectories


def diff_tool_calls(
    expected: list[dict],
    actual: list[dict],
) -> list[ToolCallDiff]:
    """Compare expected tool calls against actual tool calls."""
    diffs = []

    for i, exp in enumerate(expected):
        exp_tool = exp["tool"]
        exp_args = exp.get("args", {})

        if i >= len(actual):
            diffs.append(ToolCallDiff(
                tool_name=exp_tool,
                expected_args=exp_args,
                actual_args={},
                match=False,
                reason=f"Expected tool call #{i+1} ({exp_tool}) was not made",
            ))
            continue

        act = actual[i]
        act_tool = act.get("tool_name", act.get("name", ""))
        act_args = act.get("args", act.get("arguments", {}))

        if exp_tool != act_tool:
            diffs.append(ToolCallDiff(
                tool_name=exp_tool,
                expected_args=exp_args,
                actual_args=act_args,
                match=False,
                reason=f"Expected '{exp_tool}' but got '{act_tool}'",
            ))
            continue

        args_match = True
        mismatched_keys = []
        for key, val in exp_args.items():
            if key not in act_args:
                args_match = False
                mismatched_keys.append(f"missing '{key}'")
            elif act_args[key] != val:
                args_match = False
                mismatched_keys.append(f"'{key}': expected {val!r}, got {act_args[key]!r}")

        diffs.append(ToolCallDiff(
            tool_name=exp_tool,
            expected_args=exp_args,
            actual_args=act_args,
            match=args_match,
            reason="; ".join(mismatched_keys) if mismatched_keys else "",
        ))

    if len(actual) > len(expected):
        for i in range(len(expected), len(actual)):
            act = actual[i]
            diffs.append(ToolCallDiff(
                tool_name=act.get("tool_name", act.get("name", "?")),
                expected_args={},
                actual_args=act.get("args", act.get("arguments", {})),
                match=False,
                reason=f"Unexpected extra tool call #{i+1}",
            ))

    return diffs


async def replay_trajectory(
    trajectory: dict,
    llm_client: Any = None,
    database_url: str = "postgresql://test:test@localhost/test",
) -> TrajectoryResult:
    """Replay a trajectory by running the agent with the given LLM client.

    If no llm_client is provided, the function returns a result with
    tool_call_diffs based purely on the expected sequence (for unit testing
    the diff logic itself).
    """
    result = TrajectoryResult(
        trajectory_id=trajectory["id"],
        prompt=trajectory["prompt"],
        tool_calls_made=[],
    )

    expected_calls = trajectory.get("expected_tool_calls", [])

    if llm_client is None:
        result.tool_call_diffs = diff_tool_calls(expected_calls, [])
        result.errors.append("No LLM client provided — diff only")
        return result

    from apps.agent_runtime.state_machine import AgentStateMachine
    from packages.schemas.models import AgentState

    sm = AgentStateMachine(
        session_id="replay-test",
        task=trajectory["prompt"],
        model=trajectory.get("model", "qwen3:8b"),
        llm_client=llm_client,
        database_url=database_url,
        max_iterations=15,
    )

    states_visited = []
    async for event in sm.run():
        event_data = json.loads(event.split("data: ", 1)[1].split("\n\n")[0]) if "data: " in event else {}
        if event_data.get("type") == "tool_call":
            result.tool_calls_made.append({
                "tool_name": event_data.get("tool_name", ""),
                "args": event_data.get("tool_args", {}),
            })
        if event_data.get("state"):
            states_visited.append(event_data["state"])

    result.states_visited = states_visited
    result.completed = sm.state == AgentState.DONE
    result.tool_call_diffs = diff_tool_calls(expected_calls, result.tool_calls_made)

    return result


# ---------------------------------------------------------------------------
# Pytest integration
# ---------------------------------------------------------------------------

def _trajectory_ids() -> list[str]:
    """Return IDs of all golden trajectories for pytest parametrization."""
    ids = []
    for p in sorted(TRAJECTORIES_DIR.glob("trajectory_*.json")):
        t = load_trajectory(p)
        ids.append(t["id"])
    return ids


@pytest.mark.parametrize(
    "trajectory_path",
    [str(p) for p in sorted(TRAJECTORIES_DIR.glob("trajectory_*.json"))],
    ids=_trajectory_ids(),
)
class TestGoldenTrajectory:
    def test_trajectory_file_valid_json(self, trajectory_path):
        """Trajectory file must be valid JSON with required fields."""
        t = load_trajectory(trajectory_path)
        assert "id" in t
        assert "prompt" in t
        assert "expected_tool_calls" in t
        assert isinstance(t["expected_tool_calls"], list)
        assert len(t["expected_tool_calls"]) > 0

    def test_trajectory_has_expected_fields(self, trajectory_path):
        """Each expected tool call must have 'tool' and 'args'."""
        t = load_trajectory(trajectory_path)
        for tc in t["expected_tool_calls"]:
            assert "tool" in tc, f"Missing 'tool' in: {tc}"
            assert "args" in tc, f"Missing 'args' in: {tc}"

    def test_trajectory_tool_names_are_strings(self, trajectory_path):
        t = load_trajectory(trajectory_path)
        for tc in t["expected_tool_calls"]:
            assert isinstance(tc["tool"], str)
            assert len(tc["tool"]) > 0

    def test_diff_empty_actual(self, trajectory_path):
        """Diffing with no actual calls should flag all expected as missing."""
        t = load_trajectory(trajectory_path)
        diffs = diff_tool_calls(t["expected_tool_calls"], [])
        assert all(not d.match for d in diffs)
        assert len(diffs) == len(t["expected_tool_calls"])

    def test_diff_perfect_match(self, trajectory_path):
        """Diffing expected against itself should all match."""
        t = load_trajectory(trajectory_path)
        actual = [
            {"tool_name": tc["tool"], "args": tc["args"]}
            for tc in t["expected_tool_calls"]
        ]
        diffs = diff_tool_calls(t["expected_tool_calls"], actual)
        assert all(d.match for d in diffs)


def test_no_duplicate_trajectory_ids():
    """All trajectory IDs must be unique."""
    trajectories = load_all_trajectories()
    ids = [t["id"] for t in trajectories]
    assert len(ids) == len(set(ids)), f"Duplicate trajectory IDs: {ids}"


def test_trajectory_ids_are_sequential():
    """Trajectory IDs should be sequential (trajectory_001, trajectory_002, ...)."""
    trajectories = load_all_trajectories()
    ids = sorted(t["id"] for t in trajectories)
    for i, tid in enumerate(ids, 1):
        assert tid == f"trajectory_{i:03d}", f"Expected trajectory_{i:03d}, got {tid}"
