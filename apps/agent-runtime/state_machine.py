"""Explicit agent state machine: PLANNING → TOOL_CALL → SANDBOX_EXEC → VERIFY → (APPROVAL_PENDING) → DONE | FAILED."""

from __future__ import annotations

import difflib
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator

from apps.agent_runtime.approval import (
    request_approval,
    wait_for_decision,
)
from apps.agent_runtime.context import compress_messages
from apps.agent_runtime.llm_client import LLMClient
from packages.schemas.models import AgentEvent, AgentState
from packages.tool_registry import get_all_tools, get_tool
from packages.tool_registry.sandbox import Sandbox

logger = logging.getLogger(__name__)

STUCK_LOOP_THRESHOLD = 3
MAX_TOOL_OUTPUT = 4000

_sandbox = Sandbox(workspace_root=os.getenv("WORKSPACE_ROOT", "/workspace"))


def _policy_precheck(tool_def, tool_args: dict) -> str | None:
    """Return an error string if the call should be blocked, else None."""
    policy = tool_def.sandbox_policy
    if "path" in tool_args and policy.filesystem_scope != "":
        if not _sandbox.validate_path(str(tool_args["path"]), policy):
            return "Permission denied. Target path lies outside sandbox."
    if "command" in tool_args and not policy.network_access:
        if not _sandbox.validate_command(str(tool_args["command"]), policy):
            return "Permission denied. Command requires network access, which this sandbox policy disallows."
    return None


def _sse(event: AgentEvent) -> str:
    return f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"


class AgentStateMachine:
    def __init__(
        self,
        session_id: str,
        task: str,
        model: str,
        llm_client: LLMClient,
        database_url: str,
        max_iterations: int = 15,
        rag_context: str = "",
        images: list[str] | None = None,
    ):
        self.session_id = session_id
        self.task = task
        self.model = model
        self.llm = llm_client
        self.db_url = database_url
        self.max_iterations = max_iterations
        self.rag_context = rag_context
        self.images = images or []

        self.state = AgentState.PLANNING
        self.messages: list[dict] = []
        self.iteration = 0
        self.pending_tool_call: dict | None = None
        self.tool_result: str = ""
        self.recent_tool_calls: list[str] = []
        self.consecutive_errors = 0

    async def run(self) -> AsyncGenerator[str, None]:
        """Main agent loop — yields SSE event strings."""
        tools = get_all_tools()
        tool_schemas = self._build_tool_schemas(tools)

        system_prompt = self._build_system_prompt(tools)

        # Auto-switch to vision model when images are attached
        if self.images:
            vision_models = ["llama3.2-vision:11b", "llava", "minicpm-v"]
            current_is_vision = any(vm in self.model.lower() for vm in ["llava", "llama3.2-vision", "minicpm-v", "gemma4"])
            if not current_is_vision:
                # Try to find a vision model
                for vm in vision_models:
                    if vm in self.model or "vision" in vm:
                        self.model = vm
                        break
                else:
                    # Default to llama3.2-vision if available
                    self.model = "llama3.2-vision:11b"
                yield _sse(AgentEvent(type="state_change", state=AgentState.PLANNING, content=f"Switched to vision model: {self.model}"))

        # Build user message with optional images
        user_msg: dict = {"role": "user", "content": self.task}
        if self.images:
            user_msg["images"] = self.images

        self.messages = [
            {"role": "system", "content": system_prompt},
            user_msg,
        ]

        # Emit user message event so frontend can display it
        user_event = AgentEvent(type="user_message", content=self.task)
        if self.images:
            user_event.content = f"{self.task}\n\n[{len(self.images)} image(s) attached]"
        yield _sse(user_event)

        yield _sse(AgentEvent(type="state_change", state=AgentState.PLANNING, content="Starting agent loop"))

        while self.state not in (AgentState.DONE, AgentState.FAILED):
            self.iteration += 1
            if self.iteration > self.max_iterations:
                self.state = AgentState.FAILED
                yield _sse(AgentEvent(type="error", error="Max iterations reached", state=AgentState.FAILED))
                break

            yield _sse(AgentEvent(type="state_change", state=self.state, content=f"Iteration {self.iteration}/{self.max_iterations}"))

            match self.state:
                case AgentState.PLANNING:
                    async for event in self._plan(tool_schemas):
                        yield event
                case AgentState.TOOL_CALL:
                    async for event in self._parse_tool():
                        yield event
                case AgentState.SANDBOX_EXEC:
                    async for event in self._execute():
                        yield event
                case AgentState.VERIFY:
                    async for event in self._verify():
                        yield event
                case AgentState.APPROVAL_PENDING:
                    async for event in self._wait_approval():
                        yield event
                case _:
                    self.state = AgentState.FAILED
                    yield _sse(AgentEvent(type="error", error=f"Unexpected state: {self.state}"))

    async def _plan(self, tool_schemas: list[dict]) -> AsyncGenerator[str, None]:
        """Call LLM with native tool-calling."""
        self.messages = compress_messages(self.messages)

        try:
            response = await self.llm.chat(
                messages=self.messages,
                model=self.model,
                tools=tool_schemas if tool_schemas else None,
                temperature=0.5,
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            error_msg = str(e)
            # If it's a 400 error, the model likely doesn't support the request
            if "400" in error_msg or "Bad Request" in error_msg:
                yield _sse(AgentEvent(type="error", error=f"Model '{self.model}' returned an error. Try a different model (e.g., llama3.2-vision:11b for images). Error: {error_msg}", state=AgentState.FAILED))
            else:
                yield _sse(AgentEvent(type="error", error=str(e), state=AgentState.FAILED))
            self.state = AgentState.FAILED
            return

        if response.tool_calls:
            self.pending_tool_call = response.tool_calls[0]
            self.messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": response.tool_calls,
            })
            self.state = AgentState.TOOL_CALL
        else:
            if response.content:
                yield _sse(AgentEvent(type="text", content=response.content))
                self.messages.append({"role": "assistant", "content": response.content})
            else:
                # Empty response — model didn't produce anything
                yield _sse(AgentEvent(type="text", content="I didn't generate a response. The model may not support this request."))
            self.state = AgentState.DONE

    async def _parse_tool(self) -> AsyncGenerator[str, None]:
        """Validate and prepare the tool call."""
        if not self.pending_tool_call:
            self.state = AgentState.FAILED
            yield _sse(AgentEvent(type="error", error="No pending tool call"))
            return

        tool_name = self.pending_tool_call.get("name", "")
        tool_args = self.pending_tool_call.get("arguments", {})

        tool_def = get_tool(tool_name)
        if not tool_def:
            error = f"Unknown tool: {tool_name}"
            yield _sse(AgentEvent(type="error", error=error))
            self.messages.append({"role": "user", "content": f"Error: {error}"})
            self.state = AgentState.PLANNING
            return

        yield _sse(AgentEvent(
            type="tool_call",
            tool_name=tool_name,
            tool_args=tool_args,
            state=AgentState.TOOL_CALL,
        ))

        if tool_def.requires_approval:
            self.state = AgentState.APPROVAL_PENDING
        else:
            self.state = AgentState.SANDBOX_EXEC

    async def _execute(self) -> AsyncGenerator[str, None]:
        """Execute the tool (directly for now, sandbox in M3)."""
        if not self.pending_tool_call:
            self.state = AgentState.FAILED
            return

        tool_name = self.pending_tool_call.get("name", "")
        tool_args = self.pending_tool_call.get("arguments", {})

        # Stuck-loop detection
        self.recent_tool_calls.append(tool_name)
        if len(self.recent_tool_calls) > 3:
            self.recent_tool_calls.pop(0)
        if len(self.recent_tool_calls) == 3 and len(set(self.recent_tool_calls)) == 1:
            self.consecutive_errors += 1
            if self.consecutive_errors >= 2:
                yield _sse(AgentEvent(type="error", error=f"Stuck loop: repeated '{tool_name}' {self.consecutive_errors} times. Stopping to prevent infinite loop."))
                self.state = AgentState.FAILED
                return
            self.messages.append({
                "role": "user",
                "content": f"Notice: You've used '{tool_name}' {self.consecutive_errors} times with similar results. Try a different approach.",
            })
        else:
            self.consecutive_errors = max(0, self.consecutive_errors - 1)

        # Execute the tool handler directly
        tool_def = get_tool(tool_name)
        if not tool_def or not tool_def.handler:
            self.tool_result = f"Tool '{tool_name}' has no handler"
            self.state = AgentState.VERIFY
            yield _sse(AgentEvent(type="tool_result", tool_name=tool_name, tool_result=self.tool_result))
            return

        policy_violation = _policy_precheck(tool_def, tool_args)
        if policy_violation:
            self.tool_result = f"Tool error: {policy_violation}"
            yield _sse(AgentEvent(type="tool_result", tool_name=tool_name, tool_result=self.tool_result))
            self.state = AgentState.VERIFY
            return

        try:
            result = tool_def.handler(**tool_args)
            if hasattr(result, '__await__'):
                result = await result
            self.tool_result = str(result)
        except Exception as e:
            self.tool_result = f"Tool error: {e}"
            logger.error(f"Tool '{tool_name}' failed: {e}")

        if len(self.tool_result) > MAX_TOOL_OUTPUT:
            self.tool_result = self.tool_result[:MAX_TOOL_OUTPUT] + f"\n... [Truncated, {len(self.tool_result)} total]"

        yield _sse(AgentEvent(type="tool_result", tool_name=tool_name, tool_result=self.tool_result))
        self.state = AgentState.VERIFY

    async def _verify(self) -> AsyncGenerator[str, None]:
        """Check result and decide next state."""
        if not self.pending_tool_call:
            self.state = AgentState.DONE
            return

        tool_name = self.pending_tool_call.get("name", "")

        # "done" tool means the agent thinks it's finished
        if tool_name == "done":
            summary = self.pending_tool_call.get("arguments", {}).get("summary", "Task completed")
            yield _sse(AgentEvent(type="text", content=summary))
            self.state = AgentState.DONE
            return

        # Feed result back to LLM for next planning step
        self.messages.append({
            "role": "user",
            "content": f"Tool '{tool_name}' result:\n{self.tool_result}",
        })

        self.pending_tool_call = None
        self.state = AgentState.PLANNING

    async def _wait_approval(self) -> AsyncGenerator[str, None]:
        """Emit an approval SSE event and block on Postgres LISTEN/NOTIFY."""
        if not self.pending_tool_call:
            self.state = AgentState.FAILED
            yield _sse(AgentEvent(type="error", error="No pending tool call for approval"))
            return

        tool_name = self.pending_tool_call.get("name", "")
        tool_args = self.pending_tool_call.get("arguments", {})

        # Build approval content for the frontend
        diff_content, display_content, command = self._build_approval_content(tool_name, tool_args)

        # Persist tool_call to DB and request approval
        tool_call_id = str(uuid.uuid4())
        await request_approval(
            database_url=self.db_url,
            tool_call_id=tool_call_id,
            session_id=self.session_id,
            tool_name=tool_name,
            tool_args=tool_args,
            diff=diff_content,
            content=display_content,
            command=command,
        )

        # Emit SSE event for frontend
        event_data = {
            "tool_call_id": tool_call_id,
            "session_id": self.session_id,
            "tool_name": tool_name,
        }
        if tool_name == "run_command":
            event_data["type"] = "awaiting_command_run"
            event_data["command"] = command
        else:
            event_data["type"] = "awaiting_file_write"
            event_data["path"] = tool_args.get("path", "")
            event_data["content"] = display_content
            if diff_content:
                event_data["diff"] = diff_content

        yield _sse(AgentEvent(**event_data))

        # Block until approved or rejected
        approved = await wait_for_decision(
            database_url=self.db_url,
            tool_call_id=tool_call_id,
            timeout=600.0,
        )

        if approved:
            # Execute the tool now that it's approved
            yield _sse(AgentEvent(type="state_change", state=AgentState.APPLY, content="Approved — executing"))
            await self._execute_tool_direct(tool_name, tool_args)
            yield _sse(AgentEvent(type="tool_result", tool_name=tool_name, tool_result=self.tool_result))
            self.state = AgentState.VERIFY
        else:
            feedback = "Rejected by user."
            self.tool_result = f"Error: {tool_name} rejected. Feedback: {feedback}"
            yield _sse(AgentEvent(type="tool_result", tool_name=tool_name, tool_result=self.tool_result, is_error=True))
            self.state = AgentState.VERIFY

    def _build_approval_content(self, tool_name: str, tool_args: dict) -> tuple[str, str, str]:
        """Build diff, display content, and command strings for approval rendering."""
        diff_content = ""
        display_content = ""
        command = ""

        if tool_name == "run_command":
            command = tool_args.get("command", "")
            display_content = command
        elif tool_name == "write_file":
            path = tool_args.get("path", "")
            new_content = tool_args.get("content", "")
            old_content = self._read_file_safe(path)
            if old_content is not None:
                diff_content = self._build_diff(path, old_content, new_content)
            display_content = new_content
        elif tool_name == "edit_file":
            path = tool_args.get("path", "")
            old_text = tool_args.get("old_text", "")
            new_text = tool_args.get("new_text", "")
            diff_content = self._build_edit_diff(path, old_text, new_text)
            display_content = f"old:\n{old_text}\n\nnew:\n{new_text}"
        elif tool_name == "multi_replace":
            path = tool_args.get("path", "")
            replacements = tool_args.get("replacements", [])
            diff_content = self._build_multi_diff(path, replacements)
            display_content = f"{len(replacements)} replacement(s) in {path}"
        elif tool_name == "create_file":
            path = tool_args.get("path", "")
            display_content = tool_args.get("content", "")
        elif tool_name == "delete_file":
            path = tool_args.get("path", "")
            display_content = f"Delete: {path}"
        elif tool_name == "make_directory":
            path = tool_args.get("path", "")
            display_content = f"Create directory: {path}"

        return diff_content, display_content, command

    def _read_file_safe(self, path: str) -> str | None:
        """Read a file from the workspace, returning None if not found."""
        workspace = os.getenv("WORKSPACE_ROOT", "/workspace")
        abs_path = os.path.realpath(os.path.join(workspace, path))
        if not abs_path.startswith(os.path.realpath(workspace)):
            return None
        try:
            with open(abs_path, encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, PermissionError):
            return None

    @staticmethod
    def _build_diff(path: str, old: str, new: str) -> str:
        """Build a unified diff for write_file operations."""
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        )
        return "".join(diff)

    @staticmethod
    def _build_edit_diff(path: str, old_text: str, new_text: str) -> str:
        """Build a diff display for edit_file operations."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{path} (old)",
            tofile=f"b/{path} (new)",
            lineterm="",
        )
        return "".join(diff)

    @staticmethod
    def _build_multi_diff(path: str, replacements: list[dict]) -> str:
        """Build a summary diff for multi_replace operations."""
        parts = []
        for i, repl in enumerate(replacements[:5], 1):
            old_t = repl.get("old_text", "")[:120]
            new_t = repl.get("new_text", "")[:120]
            parts.append(f"--- Replacement {i} ---\n- {old_t}\n+ {new_t}")
        if len(replacements) > 5:
            parts.append(f"... and {len(replacements) - 5} more")
        return "\n\n".join(parts)

    async def _execute_tool_direct(self, tool_name: str, tool_args: dict) -> None:
        """Execute a tool directly (after approval)."""
        tool_def = get_tool(tool_name)
        if not tool_def or not tool_def.handler:
            self.tool_result = f"Tool '{tool_name}' has no handler"
            return

        policy_violation = _policy_precheck(tool_def, tool_args)
        if policy_violation:
            self.tool_result = f"Tool error: {policy_violation}"
            return

        try:
            result = tool_def.handler(**tool_args)
            if hasattr(result, '__await__'):
                result = await result
            self.tool_result = str(result)
        except Exception as e:
            self.tool_result = f"Tool error: {e}"
            logger.error(f"Tool '{tool_name}' failed after approval: {e}")

        if len(self.tool_result) > MAX_TOOL_OUTPUT:
            self.tool_result = self.tool_result[:MAX_TOOL_OUTPUT] + f"\n... [Truncated, {len(self.tool_result)} total]"

    def _build_system_prompt(self, tools: dict) -> str:
        tool_descs = []
        for name, tdef in tools.items():
            params = json.dumps(tdef.input_schema.get("properties", {}), indent=2)
            tool_descs.append(f"- **{name}**: {tdef.description}\n  Parameters: {params}")

        tools_section = "\n".join(tool_descs) if tool_descs else "No tools available."

        prompt = (
            "You are Spark Agent, an autonomous AI coding assistant.\n"
            "Your goal is to help the user with coding, file operations, shell commands, and technical questions.\n\n"
            "=== AVAILABLE TOOLS ===\n"
            f"{tools_section}\n\n"
            "CRITICAL RULES:\n"
            "- For greetings, small talk, or general questions, respond DIRECTLY with text. Do NOT use tools.\n"
            "- Only use tools when the user explicitly asks for a file operation, code task, or shell command.\n"
            "- NEVER call hello_world or done for simple greetings.\n"
            "- When a coding task is complete, call the `done` tool with a summary.\n"
            "- Be concise and helpful.\n"
        )

        if self.rag_context:
            prompt += f"\n=== REFERENCE CONTEXT ===\n{self.rag_context}\n"

        return prompt

    @staticmethod
    def _build_tool_schemas(tools: dict) -> list[dict]:
        schemas = []
        for tdef in tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tdef.name,
                    "description": tdef.description,
                    "parameters": tdef.input_schema,
                },
            })
        return schemas
