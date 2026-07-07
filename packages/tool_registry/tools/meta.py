"""Meta tools for agent control flow."""

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool


@tool(
    "done",
    "Call this when the task is complete. Provides a summary of what was accomplished.",
    sandbox_policy=SandboxPolicy(timeout_seconds=5),
)
def done(summary: str) -> str:
    """Signal task completion with a summary.

    Args:
        summary: A concise summary of what was accomplished.
    """
    return f"Task completed: {summary}"
