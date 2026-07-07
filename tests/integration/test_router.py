"""Integration tests for intent routing via native tool-calling."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from apps.agent_runtime.llm_client import LLMClient, LLMResponse
from apps.agent_runtime.router import ROUTING_SYSTEM_PROMPT, route_message


@pytest.mark.asyncio
class TestRouteMessage:
    async def test_route_returns_response(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(
            content="Here is your answer.",
            tool_calls=[],
            tokens_used=10,
            model="test-model",
        ))

        response = await route_message(
            client=mock_client,
            message="What is the weather?",
            model="test-model",
        )
        assert isinstance(response, LLMResponse)
        assert response.content == "Here is your answer."

    async def test_route_includes_system_prompt(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(
            content="OK",
            tool_calls=[],
            model="test-model",
        ))

        await route_message(client=mock_client, message="Hello", model="test-model")

        call_args = mock_client.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        assert messages[0]["role"] == "system"
        assert "Spark Router" in messages[0]["content"]

    async def test_route_includes_user_message(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(content="OK", model="m"))

        await route_message(client=mock_client, message="Tell me a joke", model="m")

        call_args = mock_client.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) >= 1
        assert user_msgs[-1]["content"] == "Tell me a joke"

    async def test_route_with_history(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(content="OK", model="m"))

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        await route_message(client=mock_client, message="Goodbye", history=history, model="m")

        call_args = mock_client.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        assert len(messages) >= 5

    async def test_route_history_truncated(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(content="OK", model="m"))

        history = [
            {"role": "user", "content": f"message {i}"}
            for i in range(20)
        ]

        await route_message(client=mock_client, message="latest", history=history, model="m")

        call_args = mock_client.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        assert len(messages) <= 11

    async def test_route_tool_call_response(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(
            content="Let me search for that.",
            tool_calls=[{"name": "web_search", "arguments": {"query": "python async"}}],
            model="m",
        ))

        response = await route_message(client=mock_client, message="Search for python async", model="m")
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "web_search"

    async def test_route_includes_tools(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(content="OK", model="m"))

        await route_message(client=mock_client, message="test", model="m")

        call_args = mock_client.chat.call_args
        tools = call_args.kwargs.get("tools") or call_args[1].get("tools")
        assert tools is not None
        assert len(tools) > 0

    async def test_route_temperature(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(content="OK", model="m"))

        await route_message(client=mock_client, message="test", model="m")

        call_args = mock_client.chat.call_args
        temp = call_args.kwargs.get("temperature") or call_args[1].get("temperature")
        assert temp == 0.3

    async def test_route_with_images(self):
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=LLMResponse(content="OK", model="m"))

        await route_message(
            client=mock_client,
            message="Describe this image",
            model="m",
            images=["base64encodedimage"],
        )

        call_args = mock_client.chat.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        user_msg = [m for m in messages if m["role"] == "user"][-1]
        assert "images" in user_msg

    async def test_route_system_prompt_contains_dispatcher(self):
        assert "dispatcher" in ROUTING_SYSTEM_PROMPT.lower() or "router" in ROUTING_SYSTEM_PROMPT.lower()
        assert "tool" in ROUTING_SYSTEM_PROMPT.lower()
        assert "chat" in ROUTING_SYSTEM_PROMPT.lower()


class TestLLMClient:
    def test_build_ollama_payload(self):
        client = LLMClient(ollama_url="http://localhost:11434")
        payload = client._build_ollama_payload(
            messages=[{"role": "user", "content": "hi"}],
            model="qwen3:8b",
            tools=[{"type": "function", "function": {"name": "test"}}],
            temperature=0.5,
        )
        assert payload["model"] == "qwen3:8b"
        assert payload["messages"] == [{"role": "user", "content": "hi"}]
        assert "tools" in payload
        assert payload["options"]["temperature"] == 0.5

    def test_build_ollama_payload_no_tools(self):
        client = LLMClient(ollama_url="http://localhost:11434")
        payload = client._build_ollama_payload(
            messages=[{"role": "user", "content": "hi"}],
            model="m",
            tools=None,
            temperature=0.7,
        )
        assert "tools" not in payload

    def test_parse_ollama_response_text_only(self):
        client = LLMClient(ollama_url="http://localhost:11434")
        data = {
            "message": {
                "content": "Hello there!",
                "tool_calls": [],
            }
        }
        resp = client._parse_ollama_response(data, "m")
        assert resp.content == "Hello there!"
        assert resp.tool_calls == []

    def test_parse_ollama_response_with_tools(self):
        client = LLMClient(ollama_url="http://localhost:11434")
        data = {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "read_file",
                            "arguments": {"path": "test.py"},
                        }
                    }
                ],
            }
        }
        resp = client._parse_ollama_response(data, "m")
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0]["name"] == "read_file"
        assert resp.tool_calls[0]["arguments"]["path"] == "test.py"

    def test_estimate_tokens(self):
        assert LLMClient._estimate_tokens("1234") == 1
        assert LLMClient._estimate_tokens("12345678") == 2
