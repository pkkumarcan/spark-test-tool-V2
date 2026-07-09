from __future__ import annotations

from packages.schemas.models import SandboxPolicy
from packages.tool_registry.paths import is_within_root


class Sandbox:
    """Validates tool calls against sandbox policies."""

    def __init__(self, workspace_root: str = "/workspace"):
        self.workspace_root = workspace_root

    def validate_path(self, path: str, policy: SandboxPolicy) -> bool:
        """Check that a file path falls within the allowed scope."""
        if policy.filesystem_scope == "none":
            return False
        if policy.filesystem_scope == "workspace":
            return is_within_root(path, self.workspace_root)
        return True

    def validate_command(self, command: str, policy: SandboxPolicy) -> bool:
        """Check that a command is allowed under the sandbox policy."""
        if not policy.network_access:
            network_commands = {"curl", "wget", "ssh", "nc", "netcat"}
            first_token = command.split()[0] if command.split() else ""
            if first_token in network_commands:
                return False
        return True
