"""Analysis tools: list_symbols (AST), get_diagnostics (ruff), run_tests (pytest)."""

import ast
import os
import shlex
import subprocess

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool

_WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")


def _safe_path(path: str) -> bool:
    abs_path = os.path.realpath(os.path.join(_WORKSPACE_ROOT, path))
    return abs_path.startswith(os.path.realpath(_WORKSPACE_ROOT))


def _abs(path: str) -> str:
    return os.path.realpath(os.path.join(_WORKSPACE_ROOT, path))


@tool(
    "list_symbols",
    "List all functions, classes, and variables in a Python file using AST parsing.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=5),
)
def list_symbols(path: str) -> str:
    if not path:
        return "Error: path is required."
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    abs_path = _abs(path)

    if not os.path.exists(abs_path):
        return f"Error: File '{path}' does not exist."
    if not path.endswith(".py"):
        return f"Error: '{path}' is not a Python file."

    with open(abs_path, encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    symbols = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            symbols.append(f"def {node.name}({', '.join(args)}) @ line {node.lineno}")
        elif isinstance(node, ast.AsyncFunctionDef):
            args = [a.arg for a in node.args.args]
            symbols.append(f"async def {node.name}({', '.join(args)}) @ line {node.lineno}")
        elif isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
            bases_str = f"({', '.join(bases)})" if bases else ""
            symbols.append(f"class {node.name}{bases_str} @ line {node.lineno}")
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.append(f"{target.id} = ... @ line {node.lineno}")

    if not symbols:
        return f"No symbols found in '{path}'."
    return "\n".join(symbols)


@tool(
    "get_diagnostics",
    "Run lint/type diagnostics on a file or directory using py_compile or ruff.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=30),
)
def get_diagnostics(path: str | None = None) -> str:
    abs_path = _abs(path) if path else _WORKSPACE_ROOT

    if path and not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."
    if path and not os.path.exists(abs_path):
        return f"Error: Path '{path}' does not exist."

    try:
        if path and os.path.isfile(abs_path):
            res = subprocess.run(
                ["python", "-m", "py_compile", abs_path],
                capture_output=True, text=True, timeout=30,
            )
            if res.returncode == 0:
                return f"No compilation errors in '{path}'."
            return f"Compilation errors:\n{res.stderr}"

        res = subprocess.run(
            ["ruff", "check", "--output-format=text", abs_path if path else "."],
            cwd=_WORKSPACE_ROOT,
            capture_output=True, text=True, timeout=60,
        )
        output = ""
        if res.stdout:
            output += res.stdout
        if res.stderr:
            output += res.stderr
        if not output.strip():
            return "No lint issues found."
        return output
    except FileNotFoundError:
        return "Error: 'ruff' not installed. Install with: pip install ruff"
    except Exception as e:
        return f"Error running diagnostics: {e}"


@tool(
    "run_tests",
    "Run pytest on the workspace or a specific test path.",
    sandbox_policy=SandboxPolicy(filesystem_scope="workspace", timeout_seconds=60),
)
def run_tests(test_path: str | None = None) -> str:
    cmd = "pytest"
    if test_path:
        cmd = f"pytest {shlex.quote(test_path)}"
    return _run(cmd)


def _run(command: str) -> str:
    """Internal helper to run a command via shell tool."""
    from packages.tool_registry.tools.shell import run_command
    return run_command(command=command)
