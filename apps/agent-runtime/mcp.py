"""MCP (Model Context Protocol) agent — routes tool calls to external MCP servers."""

from __future__ import annotations

import logging

import httpx

from apps.agent_runtime.llm_client import LLMClient

logger = logging.getLogger(__name__)

DEFAULT_MCP_SERVERS: dict[str, str] = {}


class MCPServer:
    """Client for a single MCP server."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url.rstrip("/")

    async def list_tools(self) -> list[dict]:
        """Get available tools from the MCP server."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(f"{self.url}/tools/list")
                if r.status_code == 200:
                    return r.json().get("tools", [])
        except Exception as e:
            logger.warning(f"MCP server {self.name} list_tools failed: {e}")
        return []

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call a tool on the MCP server."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    f"{self.url}/tools/call",
                    json={"name": tool_name, "arguments": arguments},
                )
                if r.status_code == 200:
                    result = r.json()
                    return result.get("content", [{}])[0].get("text", str(result))
                return f"MCP error: HTTP {r.status_code}"
        except Exception as e:
            return f"MCP error: {e}"


class MCPAgent:
    """Agent that can delegate tool calls to MCP servers."""

    def __init__(self, servers: dict[str, str] | None = None):
        self.servers: dict[str, MCPServer] = {}
        for name, url in (servers or DEFAULT_MCP_SERVERS).items():
            self.servers[name] = MCPServer(name, url)

    async def get_all_tools(self) -> list[dict]:
        """List tools from all configured MCP servers."""
        all_tools = []
        for server in self.servers.values():
            tools = await server.list_tools()
            for t in tools:
                t["mcp_server"] = server.name
            all_tools.extend(tools)
        return all_tools

    async def call_tool(self, tool_name: str, arguments: dict, server_hint: str | None = None) -> str:
        """Call a tool, routing to the correct MCP server."""
        if server_hint and server_hint in self.servers:
            return await self.servers[server_hint].call_tool(tool_name, arguments)

        for server in self.servers.values():
            tools = await server.list_tools()
            if any(t.get("name") == tool_name for t in tools):
                return await server.call_tool(tool_name, arguments)

        return f"Tool '{tool_name}' not found on any MCP server"


async def mcp_chat(
    client: LLMClient,
    message: str,
    mcp_agent: MCPAgent,
    model: str = "qwen3:8b",
) -> str:
    """Chat with MCP tool routing."""
    tools = await mcp_agent.get_all_tools()
    if not tools:
        return await _fallback_chat(client, message, model)

    tool_schemas = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("inputSchema", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]

    messages = [
        {"role": "system", "content": "You are Spark AI with access to MCP tools. Use tools when appropriate."},
        {"role": "user", "content": message},
    ]

    resp = await client.chat(messages=messages, model=model, tools=tool_schemas)
    if not resp.tool_calls:
        return resp.content

    tc = resp.tool_calls[0]
    result = await mcp_agent.call_tool(tc["name"], tc["arguments"])

    messages.append({"role": "assistant", "content": resp.content, "tool_calls": resp.tool_calls})
    messages.append({"role": "user", "content": f"Tool result:\n{result}"})

    final = await client.chat(messages=messages, model=model)
    return final.content


async def _fallback_chat(client: LLMClient, message: str, model: str) -> str:
    resp = await client.chat(
        messages=[
            {"role": "system", "content": "You are Spark AI. No MCP tools are configured."},
            {"role": "user", "content": message},
        ],
        model=model,
    )
    return resp.content
