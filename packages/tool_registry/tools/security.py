"""Security scanner tool — runs static analysis on workspace code."""

from __future__ import annotations

import json
import os
import subprocess

from packages.schemas.models import SandboxPolicy
from packages.tool_registry import tool

_WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")


def _safe_path(path: str) -> bool:
    abs_path = os.path.realpath(os.path.join(_WORKSPACE_ROOT, path))
    return abs_path.startswith(os.path.realpath(_WORKSPACE_ROOT))


@tool(
    "security_scan",
    "Run security scanner (bandit, pip-audit) on the workspace. Returns findings.",
    sandbox_policy=SandboxPolicy(
        filesystem_scope="workspace",
        timeout_seconds=120,
    ),
)
def security_scan(path: str = ".", scanner: str = "all") -> str:
    """Scan workspace for security issues.

    Args:
        path: Directory or file to scan (relative to workspace).
        scanner: Which scanner to run — 'bandit', 'pip_audit', or 'all'.
    """
    if not _safe_path(path):
        return "Error: Permission denied. Target path lies outside sandbox."

    abs_path = os.path.realpath(os.path.join(_WORKSPACE_ROOT, path))
    if not os.path.exists(abs_path):
        return f"Error: Path '{path}' does not exist."

    findings: list[dict] = []

    if scanner in ("bandit", "all"):
        findings.extend(_run_bandit(abs_path))

    if scanner in ("pip_audit", "all"):
        findings.extend(_run_pip_audit())

    if not findings:
        return "Security scan complete. No issues found."

    summary = f"Security scan found {len(findings)} issue(s):\n\n"
    for i, f in enumerate(findings, 1):
        summary += f"{i}. [{f.get('severity', '?')}] {f.get('file', '?')}:{f.get('line', '?')} — {f.get('message', '?')}\n"

    return summary


def _run_bandit(target: str) -> list[dict]:
    """Run bandit static analyzer."""
    try:
        result = subprocess.run(
            ["bandit", "-r", target, "-f", "json", "-q"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        data = json.loads(result.stdout) if result.stdout else {}
        findings = []
        for item in data.get("results", []):
            findings.append({
                "scanner": "bandit",
                "severity": item.get("issue_severity", "UNKNOWN"),
                "file": os.path.relpath(item.get("filename", ""), _WORKSPACE_ROOT),
                "line": item.get("line_number", 0),
                "message": item.get("issue_text", ""),
            })
        return findings
    except FileNotFoundError:
        return [{"scanner": "bandit", "severity": "INFO", "file": "", "line": 0, "message": "bandit not installed — pip install bandit"}]
    except subprocess.TimeoutExpired:
        return [{"scanner": "bandit", "severity": "WARN", "file": "", "line": 0, "message": "bandit timed out"}]
    except Exception as e:
        return [{"scanner": "bandit", "severity": "ERROR", "file": "", "line": 0, "message": str(e)}]


def _run_pip_audit() -> list[dict]:
    """Run pip-audit for dependency vulnerabilities."""
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        data = json.loads(result.stdout) if result.stdout else {}
        findings = []
        for dep in data.get("dependencies", []):
            if dep.get("vulns"):
                for v in dep["vulns"]:
                    findings.append({
                        "scanner": "pip_audit",
                        "severity": "HIGH",
                        "file": dep.get("name", ""),
                        "line": 0,
                        "message": f"{dep['name']}=={dep.get('version', '?')}: {v.get('id', '?')} — {v.get('description', '')[:100]}",
                    })
        return findings
    except FileNotFoundError:
        return [{"scanner": "pip_audit", "severity": "INFO", "file": "", "line": 0, "message": "pip-audit not installed — pip install pip-audit"}]
    except subprocess.TimeoutExpired:
        return [{"scanner": "pip_audit", "severity": "WARN", "file": "", "line": 0, "message": "pip-audit timed out"}]
    except Exception as e:
        return [{"scanner": "pip_audit", "severity": "ERROR", "file": "", "line": 0, "message": str(e)}]
