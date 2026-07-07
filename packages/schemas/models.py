from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────────

class SessionKind(str, Enum):
    CHAT = "chat"
    AGENTIC = "agentic"
    PIPELINE = "pipeline"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCallStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


class JobKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    D3 = "3d"
    MUSIC = "music"
    TTS = "tts"
    STT = "stt"
    MEME = "meme"
    POSTPROCESS = "postprocess"
    EXTRACTION = "extraction"
    PUBLISH = "publish"
    PIPELINE = "pipeline"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentState(str, Enum):
    PLANNING = "planning"
    TOOL_CALL = "tool_call"
    SANDBOX_EXEC = "sandbox_exec"
    VERIFY = "verify"
    APPROVAL_PENDING = "approval_pending"
    APPLY = "apply"
    DONE = "done"
    FAILED = "failed"


# ── Sandbox & Tool Definition ──────────────────────────────────────────────

class SandboxPolicy(BaseModel):
    network_access: bool = False
    filesystem_scope: str = "workspace"  # workspace | temp | none
    timeout_seconds: int = 60
    max_output_bytes: int = 1024 * 1024
    requires_gpu: bool = False


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    requires_approval: bool = False
    sandbox_policy: SandboxPolicy = Field(default_factory=SandboxPolicy)
    handler: Callable[..., Any] | None = None


# ── DB Models ──────────────────────────────────────────────────────────────

class Session(BaseModel):
    id: UUID
    user_id: str = "default"
    kind: SessionKind = SessionKind.CHAT
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    id: UUID
    session_id: UUID
    role: MessageRole
    content: str = ""
    tool_calls: list[dict[str, Any]] = []
    created_at: datetime


class ToolCall(BaseModel):
    id: UUID
    message_id: UUID
    tool_name: str
    args: dict[str, Any] = {}
    status: ToolCallStatus = ToolCallStatus.PENDING
    result: dict[str, Any] | None = None
    requires_approval: bool = False
    approved_at: datetime | None = None
    approved_by: str | None = None
    sandbox_container_id: str | None = None
    created_at: datetime


class Job(BaseModel):
    id: UUID
    kind: JobKind
    status: JobStatus = JobStatus.PENDING
    priority: int = 0
    payload: dict[str, Any] = {}
    gpu_node: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class Workspace(BaseModel):
    id: UUID
    session_id: UUID
    root_path: str
    git_remote: str | None = None
    created_at: datetime


class GPUNode(BaseModel):
    id: UUID
    name: str
    total_vram_mb: int
    free_vram_mb: int
    last_heartbeat: datetime


# ── SSE Events ─────────────────────────────────────────────────────────────

class AgentEvent(BaseModel):
    type: str  # text | tool_call | tool_result | error | state_change | awaiting_file_write | awaiting_command_run
    content: str = ""
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_result: Any = None
    state: AgentState | None = None
    error: str | None = None
    # Approval-related fields
    tool_call_id: str | None = None
    session_id: str | None = None
    path: str | None = None
    command: str | None = None
    diff: str | None = None
    is_error: bool | None = None
    status: str | None = None
    resolution: str | None = None
