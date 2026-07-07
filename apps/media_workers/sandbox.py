"""Docker sandbox execution: run tool commands in locked-down containers."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")
_DEFAULT_IMAGE = "python:3.12-slim"
_DEFAULT_MEMORY = "512m"
_DEFAULT_CPUS = "1.0"
_DEFAULT_TIMEOUT = 60


@dataclass
class SandboxConfig:
    image: str = _DEFAULT_IMAGE
    memory: str = _DEFAULT_MEMORY
    cpus: str = _DEFAULT_CPUS
    timeout: int = _DEFAULT_TIMEOUT
    network: str = "none"
    read_only: bool = True
    workspace_mount: str = _WORKSPACE_ROOT
    tmpfs_size: str = "100M"


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def output(self) -> str:
        parts = [f"Exit Code: {self.exit_code}"]
        if self.stdout:
            parts.append(f"Stdout:\n{self.stdout}")
        if self.stderr:
            parts.append(f"Stderr:\n{self.stderr}")
        if self.timed_out:
            parts.append("Timed out after timeout")
        return "\n".join(parts)


class DockerSandbox:
    """Execute tool commands inside locked-down Docker containers."""

    def __init__(self, config: SandboxConfig | None = None):
        self.config = config or SandboxConfig()
        self._docker_available: bool | None = None

    async def _check_docker(self) -> bool:
        if self._docker_available is not None:
            return self._docker_available
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "info",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            self._docker_available = proc.returncode == 0
        except FileNotFoundError:
            self._docker_available = False
        return self._docker_available

    async def run(
        self,
        command: str,
        workspace: str | None = None,
        timeout: int | None = None,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        """Run a command inside a sandboxed Docker container.

        Args:
            command: Shell command to execute.
            workspace: Workspace path to mount (defaults to config).
            timeout: Override timeout in seconds.
            env: Additional environment variables.

        Returns:
            SandboxResult with exit_code, stdout, stderr.
        """
        if not await self._check_docker():
            return await self._run_fallback(command, timeout)

        ws = workspace or self.config.workspace_mount
        timeout = timeout or self.config.timeout

        env_args = []
        if env:
            for k, v in env.items():
                env_args.extend(["-e", f"{k}={v}"])

        docker_cmd = [
            "docker", "run", "--rm",
            "--network", self.config.network,
            "--memory", self.config.memory,
            "--cpus", self.config.cpus,
            "--read-only",
            "--tmpfs", f"/tmp:size={self.config.tmpfs_size}",
            "-v", f"{ws}:/workspace:rw",
            *env_args,
            self.config.image,
            "sh", "-c", command,
        ]

        logger.debug(f"Sandbox exec: {' '.join(docker_cmd)}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return SandboxResult(
                exit_code=proc.returncode or 0,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
            )
        except TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                timed_out=True,
            )
        except Exception as e:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox error: {e}",
            )

    async def _run_fallback(
        self, command: str, timeout: int | None = None
    ) -> SandboxResult:
        """Fallback to subprocess when Docker is not available."""
        timeout = timeout or self.config.timeout
        logger.warning("Docker not available — falling back to subprocess execution")

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=self.config.workspace_mount,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return SandboxResult(
                exit_code=proc.returncode or 0,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
            )
        except TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                timed_out=True,
            )
        except Exception as e:
            return SandboxResult(
                exit_code=-1,
                stdout="",
                stderr=f"Fallback error: {e}",
            )

    async def run_tool(
        self,
        tool_handler: Any,
        tool_args: dict[str, Any],
        timeout: int | None = None,
    ) -> SandboxResult:
        """Execute a tool handler, wrapping it in sandbox execution.

        For file operations, runs directly. For shell commands,
        wraps in Docker container.
        """
        tool_name = getattr(tool_handler, "_tool_name", "unknown")

        # Shell commands go through Docker
        if tool_name == "run_command":
            command = tool_args.get("command", "")
            cmd_timeout = tool_args.get("timeout", timeout or self.config.timeout)
            return await self.run(command, timeout=cmd_timeout)

        # File operations run directly (sandbox policy enforced at path level)
        try:
            result = tool_handler(**tool_args)
            if hasattr(result, "__await__"):
                result = await result
            return SandboxResult(exit_code=0, stdout=str(result), stderr="")
        except Exception as e:
            return SandboxResult(exit_code=1, stdout="", stderr=str(e))
