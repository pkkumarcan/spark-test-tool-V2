"""Shell command tool with security checks."""

import os
import re
import shlex
import subprocess

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool

_WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")

ALLOWED_COMMANDS = {
    "python", "python3", "pip", "pytest", "ruff", "black", "mypy", "py_compile",
    "node", "npm", "npx", "yarn", "pnpm", "bun", "vite", "tsc", "eslint", "prettier",
    "cargo", "rustc", "go",
    "ls", "cat", "echo", "head", "tail", "wc", "find", "grep", "sed", "awk",
    "sort", "uniq", "diff", "tee", "xargs", "mkdir", "cp", "mv", "touch", "cd",
    "git",
    "which", "env", "date", "uname",
}

_BLOCKED_PATTERNS = [
    r"rm\s+-rf",
    r"--delete",
    r"--force-rm",
]


def _audit_command(command: str) -> dict:
    """Analyze shell command for security violations.

    NOTE: This is a defense-in-depth layer. True network isolation for
    interpreters (python, node) is enforced at the container level
    (--network=none), not by string matching. See ADR-004 and the
    sandbox threat model doc.
    """
    violations = []
    rules = [
        (r"curl\s+.*\|\s*bash", "Piping curl directly to bash"),
        (r"wget\s+.*\|\s*bash", "Piping wget directly to bash"),
        (r"base64\s+-d\s*\|\s*bash", "Decoding obfuscated base64 payload to bash"),
        (r"/etc/passwd", "Unauthorized system password database read"),
        (r"/etc/shadow", "Unauthorized system credential read"),
        (r"curl\s+.*http://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", "Direct external IP connection bypass attempt"),
        (r"python[0-9.]*\s+-c\s+.*(socket|urllib|requests)", "Inline interpreter network call"),
        (r"\$\(.*\)|`.*`", "Command substitution attempt"),
    ]
    for regex, reason in rules:
        if re.search(regex, command, re.IGNORECASE):
            violations.append(reason)
    return {
        "status": "clean" if not violations else "alert",
        "violations": violations,
    }


@tool(
    "run_command",
    "Run a shell command with security checks. Output is captured and returned.",
    requires_approval=True,
    sandbox_policy=SandboxPolicy(
        filesystem_scope="workspace",
        timeout_seconds=60,
    ),
)
def run_command(command: str, timeout: int = 60) -> str:
    if not command:
        return "Error: command is required."

    audit = _audit_command(command)
    if audit["status"] == "alert":
        return f"Error: Command blocked by security audit. Reason: {', '.join(audit['violations'])}"

    try:
        cmd_parts = shlex.split(command)
    except ValueError as e:
        return f"Error: Invalid command syntax: {e}"

    if not cmd_parts:
        return "Error: Empty command."

    base_cmd = os.path.basename(cmd_parts[0])
    if base_cmd not in ALLOWED_COMMANDS:
        return (
            f"Error: Command '{base_cmd}' is not in the allowed command list. "
            f"Permitted commands: {', '.join(sorted(ALLOWED_COMMANDS))}"
        )

    for pat in _BLOCKED_PATTERNS:
        if re.search(pat, command, re.IGNORECASE):
            return "Error: Command rejected — dangerous flag pattern detected."

    try:
        res = subprocess.run(
            cmd_parts,
            cwd=_WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = f"Exit Code: {res.returncode}\n"
        if res.stdout:
            output += f"Stdout:\n{res.stdout}\n"
        if res.stderr:
            output += f"Stderr:\n{res.stderr}\n"
        return output
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error running command: {e}"
