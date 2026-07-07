"""Integration tests for the agent loop: planning → tool_call → verify → done."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from apps.agent_runtime.state_machine import AgentStateMachine, _sse
from packages.schemas.models import AgentEvent, AgentState
from packages.tool_registry.registry import _REGISTRY, auto_discover


@pytest.fixture(autouse=True)
def _ensure_registry():
    _REGISTRY.clear()
    auto_discover(force=True)
    yield
    _REGISTRY.clear()
    auto_discover(force=True)


@pytest.mark.asyncio
class TestAgentStateMachine:
    async def test_direct_response_no_tool(self, mock_llm):
        """Agent gets a text response and goes to DONE."""
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="What is 2+2?",
            model="test-model",
            llm_client=mock_llm,
            database_url="postgresql://test:test@localhost/test",
        )
        events = []
        async for event in sm.run():
            events.append(event)

        assert sm.state == AgentState.DONE
        text_events = [e for e in events if "text" in e]
        assert len(text_events) > 0

    async def test_tool_call_flow(self, mock_llm_tool_call):
        """Agent calls read_file, gets result, then finishes."""
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="Read test.py",
            model="test-model",
            llm_client=mock_llm_tool_call,
            database_url="postgresql://test:test@localhost/test",
        )
        events = []
        async for event in sm.run():
            events.append(event)

        tool_call_events = [e for e in events if '"type":"tool_call"' in e or '"type":"tool_result"' in e]
        assert len(tool_call_events) >= 1

    async def test_done_tool_ends_loop(self, mock_llm_done_tool):
        """Agent calls done tool and terminates."""
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="Finish the task",
            model="test-model",
            llm_client=mock_llm_done_tool,
            database_url="postgresql://test:test@localhost/test",
        )
        events = []
        async for event in sm.run():
            events.append(event)

        assert sm.state == AgentState.DONE

    async def test_max_iterations_stops(self):
        """Agent stops after max_iterations."""
        from tests.conftest import FakeLLMResponse, MockLLMClient

        responses = [
            FakeLLMResponse(
                content="retrying",
                tool_calls=[{"name": "read_file", "arguments": {"path": "x.py"}}],
            )
            for _ in range(20)
        ]
        llm = MockLLMClient(responses)
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="keep going",
            model="test-model",
            llm_client=llm,
            database_url="postgresql://test:test@localhost/test",
            max_iterations=3,
        )
        events = []
        async for event in sm.run():
            events.append(event)

        assert sm.state == AgentState.FAILED
        error_events = [e for e in events if '"type":"error"' in e]
        assert len(error_events) > 0

    async def test_unknown_tool_recovers(self):
        """Agent tries an unknown tool, gets error, recovers to PLANNING."""
        from tests.conftest import FakeLLMResponse, MockLLMClient

        llm = MockLLMClient([
            FakeLLMResponse(
                content="trying nonexistent",
                tool_calls=[{"name": "nonexistent_tool_xyz", "arguments": {}}],
            ),
            FakeLLMResponse(content="OK, done."),
        ])
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="use nonexistent tool",
            model="test-model",
            llm_client=llm,
            database_url="postgresql://test:test@localhost/test",
        )
        events = []
        async for event in sm.run():
            events.append(event)

        assert sm.state == AgentState.DONE
        error_events = [e for e in events if '"type":"error"' in e]
        assert len(error_events) > 0

    async def test_llm_failure_goes_failed(self):
        """LLM exception causes FAILED state."""

        failing_llm = AsyncMock()
        failing_llm.chat = AsyncMock(side_effect=Exception("LLM connection refused"))

        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="do something",
            model="test-model",
            llm_client=failing_llm,
            database_url="postgresql://test:test@localhost/test",
        )
        events = []
        async for event in sm.run():
            events.append(event)

        assert sm.state == AgentState.FAILED

    async def test_iteration_counter_increments(self, mock_llm_done_tool):
        """Iteration counter increments during execution."""
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="test",
            model="test-model",
            llm_client=mock_llm_done_tool,
            database_url="postgresql://test:test@localhost/test",
        )
        async for _ in sm.run():
            pass

        assert sm.iteration >= 1

    async def test_system_prompt_includes_tools(self, mock_llm):
        """System prompt includes available tool descriptions."""
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="test",
            model="test-model",
            llm_client=mock_llm,
            database_url="postgresql://test:test@localhost/test",
        )
        async for _ in sm.run():
            pass

        assert len(mock_llm.calls) > 0
        system_msg = mock_llm.calls[0]["messages"][0]
        assert system_msg["role"] == "system"
        assert "read_file" in system_msg["content"]

    async def test_sse_format(self):
        """SSE events are properly formatted."""
        event = AgentEvent(type="text", content="hello", state=AgentState.PLANNING)
        sse_str = _sse(event)
        assert sse_str.startswith("event: text")
        assert "data:" in sse_str
        assert '"content":"hello"' in sse_str

    async def test_messages_accumulate(self, mock_llm_tool_call):
        """Messages list accumulates over iterations."""
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="Read file",
            model="test-model",
            llm_client=mock_llm_tool_call,
            database_url="postgresql://test:test@localhost/test",
        )
        async for _ in sm.run():
            pass

        assert len(sm.messages) > 2

    async def test_approval_tool_goes_to_approval_state(self):
        """Tool with requires_approval=True goes to APPROVAL_PENDING."""
        from packages.tool_registry.registry import _REGISTRY, auto_discover
        from tests.conftest import FakeLLMResponse, MockLLMClient

        if "write_file" not in _REGISTRY:
            auto_discover(force=True)
        llm = MockLLMClient([
            FakeLLMResponse(
                content="Let me write that file.",
                tool_calls=[{"name": "write_file", "arguments": {"path": "test.py", "content": "new"}}],
            ),
            FakeLLMResponse(content="Done."),
        ])

        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="Write test.py",
            model="test-model",
            llm_client=llm,
            database_url="postgresql://test:test@localhost/test",
        )
        events = []
        with patch("apps.agent_runtime.state_machine.request_approval", new_callable=AsyncMock) as mock_req, \
             patch("apps.agent_runtime.state_machine.wait_for_decision", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = False
            async for event in sm.run():
                events.append(event)

        approval_events = [e for e in events if "awaiting" in e]
        assert len(approval_events) > 0

    async def test_build_system_prompt_with_rag(self, mock_llm):
        """System prompt includes RAG context when provided."""
        sm = AgentStateMachine(
            session_id=str(uuid4()),
            task="test",
            model="test-model",
            llm_client=mock_llm,
            database_url="postgresql://test:test@localhost/test",
            rag_context="Important reference data here.",
        )
        async for _ in sm.run():
            pass

        system_msg = mock_llm.calls[0]["messages"][0]
        assert "Important reference data" in system_msg["content"]
