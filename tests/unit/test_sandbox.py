"""Sandbox policy tests: network, filesystem scope, timeout, and path validation."""

from __future__ import annotations

from packages.schemas.models import SandboxPolicy
from packages.tool_registry.sandbox import Sandbox


class TestSandboxPolicyDefaults:
    def test_default_policy(self):
        p = SandboxPolicy()
        assert p.network_access is False
        assert p.filesystem_scope == "workspace"
        assert p.timeout_seconds == 60
        assert p.max_output_bytes == 1024 * 1024
        assert p.requires_gpu is False

    def test_network_policy(self):
        p = SandboxPolicy(network_access=True)
        assert p.network_access is True

    def test_no_filesystem(self):
        p = SandboxPolicy(filesystem_scope="none")
        assert p.filesystem_scope == "none"

    def test_temp_scope(self):
        p = SandboxPolicy(filesystem_scope="temp")
        assert p.filesystem_scope == "temp"

    def test_custom_timeout(self):
        p = SandboxPolicy(timeout_seconds=300)
        assert p.timeout_seconds == 300

    def test_gpu_required(self):
        p = SandboxPolicy(requires_gpu=True)
        assert p.requires_gpu is True


class TestSandboxPathValidation:
    def setup_method(self):
        self.sandbox = Sandbox(workspace_root="/workspace")

    def test_workspace_path_allowed(self):
        p = SandboxPolicy(filesystem_scope="workspace")
        assert self.sandbox.validate_path("/workspace/src/main.py", p) is True

    def test_workspace_path_subdir(self):
        p = SandboxPolicy(filesystem_scope="workspace")
        assert self.sandbox.validate_path("/workspace/a/b/c/file.txt", p) is True

    def test_workspace_root_only(self):
        p = SandboxPolicy(filesystem_scope="workspace")
        assert self.sandbox.validate_path("/workspace", p) is True

    def test_outside_workspace_denied(self):
        p = SandboxPolicy(filesystem_scope="workspace")
        assert self.sandbox.validate_path("/etc/passwd", p) is False

    def test_outside_workspace_home(self):
        p = SandboxPolicy(filesystem_scope="workspace")
        assert self.sandbox.validate_path("/home/user/secret.py", p) is False

    def test_temp_scope_allows_any(self):
        p = SandboxPolicy(filesystem_scope="temp")
        assert self.sandbox.validate_path("/any/path/at/all.txt", p) is True

    def test_none_scope_denies_all(self):
        p = SandboxPolicy(filesystem_scope="none")
        assert self.sandbox.validate_path("/workspace/file.py", p) is False
        assert self.sandbox.validate_path("/tmp/file.py", p) is False

    def test_relative_path_resolves(self):
        p = SandboxPolicy(filesystem_scope="workspace")
        assert self.sandbox.validate_path("src/main.py", p) is True

    def test_dotdot_traversal_denied(self):
        p = SandboxPolicy(filesystem_scope="workspace")
        assert self.sandbox.validate_path("/workspace/../../../etc/passwd", p) is False

    def test_symlink_escape_denied(self, workspace):
        """Test that symlink-based path traversal is caught."""
        p = SandboxPolicy(filesystem_scope="workspace")
        link = workspace / "escape_link"
        link.symlink_to("/etc")
        sandbox = Sandbox(workspace_root=str(workspace))
        assert sandbox.validate_path("escape_link/passwd", p) is False


class TestSandboxCommandValidation:
    def setup_method(self):
        self.sandbox = Sandbox(workspace_root="/workspace")

    def test_allowed_command_no_network(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("ls -la", p) is True

    def test_allowed_command_with_network(self):
        p = SandboxPolicy(network_access=True)
        assert self.sandbox.validate_command("curl http://example.com", p) is True

    def test_network_command_blocked_no_network(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("curl http://evil.com", p) is False

    def test_wget_blocked_no_network(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("wget http://evil.com/file", p) is False

    def test_ssh_blocked_no_network(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("ssh user@host", p) is False

    def test_nc_blocked_no_network(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("nc -l 4444", p) is False

    def test_netcat_blocked_no_network(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("netcat -l 4444", p) is False

    def test_python_command_allowed(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("python -c 'print(1)'", p) is True

    def test_empty_command(self):
        p = SandboxPolicy(network_access=False)
        assert self.sandbox.validate_command("", p) is True


class TestToolSandboxPolicies:
    """Verify that each tool's registered sandbox policy matches the spec."""

    def _get_tool(self, name):
        from packages.tool_registry.registry import _REGISTRY, auto_discover, get_tool
        if name not in _REGISTRY:
            auto_discover(force=True)
        return get_tool(name)

    def test_read_file_policy(self):
        t = self._get_tool("read_file")
        assert t is not None
        assert t.sandbox_policy.filesystem_scope == "workspace"
        assert t.sandbox_policy.network_access is False
        assert t.sandbox_policy.timeout_seconds == 5

    def test_write_file_policy(self):
        t = self._get_tool("write_file")
        assert t is not None
        assert t.requires_approval is True
        assert t.sandbox_policy.filesystem_scope == "workspace"

    def test_run_command_policy(self):
        t = self._get_tool("run_command")
        assert t is not None
        assert t.requires_approval is True
        assert t.sandbox_policy.timeout_seconds == 60

    def test_web_search_policy(self):
        t = self._get_tool("web_search")
        assert t is not None
        assert t.sandbox_policy.network_access is True

    def test_search_files_policy(self):
        t = self._get_tool("search_files")
        assert t is not None
        assert t.sandbox_policy.filesystem_scope == "workspace"
        assert t.sandbox_policy.network_access is False

    def test_git_status_policy(self):
        t = self._get_tool("git_status")
        assert t is not None
        assert t.sandbox_policy.filesystem_scope == "workspace"
        assert t.sandbox_policy.timeout_seconds == 30
