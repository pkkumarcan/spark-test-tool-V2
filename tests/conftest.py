"""Shared fixtures for Spark V2 tests.

Provides mock LLM client, mock ComfyUI, mock PostgreSQL,
and a temporary workspace directory for file-operation tools.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# LLM mock
# ---------------------------------------------------------------------------

class FakeLLMResponse:
    def __init__(
        self,
        content: str = "",
        tool_calls: list[dict] | None = None,
        tokens_used: int = 0,
        model: str = "test-model",
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.tokens_used = tokens_used
        self.model = model


class MockLLMClient:
    """Deterministic mock LLM client for unit/integration tests."""

    def __init__(self, responses: list[FakeLLMResponse] | None = None):
        self._responses = list(responses or [FakeLLMResponse(content="Done.")])
        self._call_count = 0
        self.calls: list[dict] = []

    async def chat(
        self,
        messages: list[dict],
        model: str = "test-model",
        tools: list[dict] | None = None,
        stream: bool = False,
        timeout: int = 120,
        temperature: float = 0.7,
    ) -> FakeLLMResponse:
        self.calls.append({
            "messages": messages,
            "model": model,
            "tools": tools,
        })
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]


@pytest.fixture
def mock_llm():
    """Default mock LLM that returns a text response (no tool calls)."""
    return MockLLMClient([FakeLLMResponse(content="I'll help you with that.")])


@pytest.fixture
def mock_llm_tool_call():
    """Mock LLM that returns a tool call, then a done response."""
    return MockLLMClient([
        FakeLLMResponse(
            content="Let me read that file.",
            tool_calls=[{"name": "read_file", "arguments": {"path": "test.py"}}],
        ),
        FakeLLMResponse(content="Done."),
    ])


@pytest.fixture
def mock_llm_done_tool():
    """Mock LLM that calls the done tool immediately."""
    return MockLLMClient([
        FakeLLMResponse(
            content="Task complete.",
            tool_calls=[{"name": "done", "arguments": {"summary": "All done."}}],
        ),
    ])


@pytest.fixture
def mock_llm_repeated():
    """Mock LLM that repeats the same tool call many times (for stuck-loop testing)."""
    return MockLLMClient([
        FakeLLMResponse(
            content="Trying again.",
            tool_calls=[{"name": "read_file", "arguments": {"path": "test.py"}}],
        )
        for _ in range(10)
    ])


# ---------------------------------------------------------------------------
# Temporary workspace — patches _WORKSPACE_ROOT in all tool modules
# ---------------------------------------------------------------------------

@pytest.fixture
def workspace(tmp_path):
    """Create a temporary workspace directory and patch _WORKSPACE_ROOT everywhere."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    ws_str = str(ws)

    import packages.tool_registry.tools.analysis as analysis_mod
    import packages.tool_registry.tools.file_ops as file_ops_mod
    import packages.tool_registry.tools.search as search_mod

    old_file_ops = file_ops_mod._WORKSPACE_ROOT
    old_search = search_mod._WORKSPACE_ROOT
    old_analysis = analysis_mod._WORKSPACE_ROOT

    file_ops_mod._WORKSPACE_ROOT = ws_str
    search_mod._WORKSPACE_ROOT = ws_str
    analysis_mod._WORKSPACE_ROOT = ws_str

    old_env = os.environ.get("WORKSPACE_ROOT")
    os.environ["WORKSPACE_ROOT"] = ws_str

    # Patch shell module — may have been reimported by auto_discover(force=True)
    import sys
    shell_key = "packages.tool_registry.tools.shell"
    if shell_key in sys.modules:
        shell_mod = sys.modules[shell_key]
        old_shell = shell_mod._WORKSPACE_ROOT
        shell_mod._WORKSPACE_ROOT = ws_str
    else:
        old_shell = None
        import packages.tool_registry.tools.shell as shell_mod_fresh
        shell_mod_fresh._WORKSPACE_ROOT = ws_str
        old_shell = shell_mod_fresh._WORKSPACE_ROOT

    yield ws

    file_ops_mod._WORKSPACE_ROOT = old_file_ops
    search_mod._WORKSPACE_ROOT = old_search
    analysis_mod._WORKSPACE_ROOT = old_analysis
    if shell_key in sys.modules:
        sys.modules[shell_key]._WORKSPACE_ROOT = old_shell if old_shell is not None else "/workspace"

    if old_env is not None:
        os.environ["WORKSPACE_ROOT"] = old_env
    else:
        os.environ.pop("WORKSPACE_ROOT", None)


@pytest.fixture
def sample_file(workspace):
    """Create a sample Python file in the workspace."""
    f = workspace / "test.py"
    f.write_text("def hello():\n    return 'world'\n")
    return f


@pytest.fixture
def sample_project(workspace):
    """Create a minimal project structure in the workspace."""
    (workspace / "src").mkdir()
    (workspace / "src" / "main.py").write_text("import os\nprint('hello')\n")
    (workspace / "src" / "utils.py").write_text("def helper():\n    pass\n")
    (workspace / "tests").mkdir()
    (workspace / "tests" / "test_main.py").write_text("def test_hello():\n    assert True\n")
    (workspace / "README.md").write_text("# Test Project\n")
    (workspace / "requirements.txt").write_text("fastapi>=0.100.0\npytest>=8.0\n")
    return workspace


# ---------------------------------------------------------------------------
# Mock ComfyUI
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_comfyui():
    """Mock ComfyUI server responses."""
    mock = MagicMock()
    mock.submit_prompt.return_value = {"prompt_id": "test-prompt-123"}
    mock.get_history.return_value = {
        "test-prompt-123": {
            "outputs": {
                "9": {
                    "images": [{"filename": "test_output.png", "subfolder": "", "type": "output"}]
                }
            }
        }
    }
    mock.get_image.return_value = b"\x89PNG\r\n\x1a\nfake-image-data"
    return mock


# ---------------------------------------------------------------------------
# Mock Postgres (asyncpg pool)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Mock asyncpg connection pool for session/approval tests."""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    conn.fetchrow.return_value = {
        "id": uuid4(),
        "user_id": "default",
        "kind": "chat",
        "status": "active",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    conn.fetch.return_value = []
    conn.execute.return_value = "UPDATE 1"
    return pool


# ---------------------------------------------------------------------------
# Agent state machine helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def make_agent_state_machine():
    """Factory fixture to create an AgentStateMachine with mocked dependencies."""
    from apps.agent_runtime.state_machine import AgentStateMachine

    def _make(
        task: str = "test task",
        model: str = "test-model",
        llm_client=None,
        max_iterations: int = 15,
        database_url: str = "postgresql://test:test@localhost/test",
    ):
        return AgentStateMachine(
            session_id=str(uuid4()),
            task=task,
            model=model,
            llm_client=llm_client or MockLLMClient(),
            database_url=database_url,
            max_iterations=max_iterations,
        )

    return _make
