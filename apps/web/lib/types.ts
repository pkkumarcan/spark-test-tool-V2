/**
 * TypeScript types matching packages/schemas/models.py.
 *
 * These types mirror the Python Pydantic models so frontend and backend
 * always agree on shapes — eliminates evt.diff vs evt.diff_html bugs.
 */

// ── Enums ──────────────────────────────────────────────────────────────────

export type SessionKind = 'chat' | 'agentic' | 'pipeline';

export type SessionStatus = 'active' | 'archived';

export type MessageRole = 'system' | 'user' | 'assistant' | 'tool';

export type ToolCallStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'awaiting_approval';

export type JobKind = 'image' | 'video' | 'audio' | '3d' | 'music' | 'pipeline';

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type AgentStateType =
  | 'planning'
  | 'tool_call'
  | 'sandbox_exec'
  | 'verify'
  | 'approval_pending'
  | 'apply'
  | 'done'
  | 'failed';

// ── Sandbox & Tool Definition ──────────────────────────────────────────────

export interface SandboxPolicy {
  network_access: boolean;
  filesystem_scope: 'workspace' | 'temp' | 'none';
  timeout_seconds: number;
  max_output_bytes: number;
  requires_gpu: boolean;
}

export interface ToolDefinition {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  requires_approval: boolean;
  sandbox_policy: SandboxPolicy;
}

// ── DB Models ──────────────────────────────────────────────────────────────

export interface Session {
  id: string;
  user_id: string;
  kind: SessionKind;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  tool_calls: ToolCallRecord[];
  created_at: string;
}

export interface ToolCallRecord {
  id: string;
  message_id: string;
  tool_name: string;
  args: Record<string, unknown>;
  status: ToolCallStatus;
  result: Record<string, unknown> | null;
  requires_approval: boolean;
  approved_at: string | null;
  approved_by: string | null;
  sandbox_container_id: string | null;
  created_at: string;
}

export interface Job {
  id: string;
  kind: JobKind;
  status: JobStatus;
  priority: number;
  payload: Record<string, unknown>;
  gpu_node: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  retry_count: number;
  max_retries: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface Workspace {
  id: string;
  session_id: string;
  root_path: string;
  git_remote: string | null;
  created_at: string;
}

export interface GPUNode {
  id: string;
  name: string;
  total_vram_mb: number;
  free_vram_mb: number;
  last_heartbeat: string;
}

// ── SSE Events ─────────────────────────────────────────────────────────────

export interface AgentEvent {
  type: string;
  content?: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  tool_result?: unknown;
  state?: AgentStateType;
  error?: string;
  status?: string;
  resolution?: string;
  diff?: string;
  path?: string;
  command?: string;
  session_id?: string;
  is_error?: boolean;
}
