"""Git tools: status, diff, log."""

import shlex

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool


def _run(cmd: str) -> str:
    from packages.tool_registry.tools.shell import run_command
    return run_command(command=cmd)


@tool(
    "git_status",
    "Run git status in the workspace.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=30),
)
def git_status() -> str:
    return _run("git status")


@tool(
    "git_diff",
    "Run git diff. Optionally diff a specific file.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=30),
)
def git_diff(path: str | None = None) -> str:
    cmd = "git diff"
    if path:
        cmd = f"git diff -- {shlex.quote(path)}"
    return _run(cmd)


@tool(
    "git_log",
    "Show recent git log entries.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=30),
)
def git_log(n: int = 10) -> str:
    return _run(f"git log --oneline -n {n}")
