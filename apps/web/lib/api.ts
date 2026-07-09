const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

export function gatewayUrl(path: string): string {
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8080${path}`;
  }
  return `${BASE_URL}${path}`;
}

export async function apiFetch<T = unknown>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`);
  }
  return resp.json() as Promise<T>;
}

// Health & GPU

export interface HealthResponse {
  services: Record<string, string>;
}

export interface GPUInfo {
  index: number;
  name: string;
  vram_used_mb: number;
  vram_total_mb: number;
  utilization_pct: number;
  temperature_c: number;
  power_w: number;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

export async function fetchGpuStatus(): Promise<Record<string, GPUInfo>> {
  const data = await apiFetch<{ gpus: Record<string, GPUInfo> }>('/api/gpu/status');
  return data.gpus || {};
}

// IDE

export interface FileEntry {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileEntry[];
}

export async function readFile(path: string): Promise<string> {
  const data = await apiFetch<{ status: string; content: string }>(
    `/api/ide/file?path=${encodeURIComponent(path)}`,
  );
  return data.content;
}

export async function writeFile(path: string, content: string): Promise<void> {
  await apiFetch('/api/ide/file', {
    method: 'POST',
    body: JSON.stringify({ path, content }),
  });
}

export async function listFiles(): Promise<FileEntry[]> {
  const data = await apiFetch<{ status: string; files: FileEntry[] }>(
    '/api/ide/files',
  );
  return data.files;
}

// Models

export interface ModelInfo {
  name: string;
  size: number;
}

export async function fetchModels(): Promise<{ models: ModelInfo[]; default: string }> {
  const data = await apiFetch<{ models: ModelInfo[]; default: string }>('/api/models');
  return data;
}

// Agent

export async function sendAgentMessage(
  task: string,
  model: string,
  sessionId: string,
  images?: string[],
): Promise<Response> {
  return fetch(`${BASE_URL}/api/orchestrator/code/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, model, session_id: sessionId, images }),
  });
}

export async function approveTool(toolCallId: string): Promise<void> {
  await apiFetch('/api/orchestrator/code/approve', {
    method: 'POST',
    body: JSON.stringify({ tool_call_id: toolCallId }),
  });
}

export async function rejectTool(
  toolCallId: string,
  feedback: string,
): Promise<void> {
  await apiFetch('/api/orchestrator/code/reject', {
    method: 'POST',
    body: JSON.stringify({ tool_call_id: toolCallId, feedback }),
  });
}

// Chat

export async function chat(message: string): Promise<{ response: string }> {
  return apiFetch('/api/text/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

// Mail

export interface Email {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
}

export async function fetchEmails(): Promise<Email[]> {
  const data = await apiFetch<{ emails: Email[] }>('/api/mail/emails');
  return data.emails || [];
}

export async function fetchMailStats(): Promise<Record<string, unknown>> {
  return apiFetch('/api/mail/stats');
}

export async function startMailSync(): Promise<void> {
  await apiFetch('/api/mail/sync/start', { method: 'POST' });
}

// Pipeline

export interface PipelineJob {
  job_id: string;
  job_code?: string;
  channel_id?: string;
  content_type?: string;
  topic?: string;
  status: string;
  current_step?: string;
  stage?: string;
  progress_pct?: number;
  updated_at?: string;
}

export async function listPipelines(): Promise<PipelineJob[]> {
  const data = await apiFetch<{ pipelines: PipelineJob[] } | PipelineJob[]>('/api/pipeline/list');
  return Array.isArray(data) ? data : data.pipelines || [];
}

export async function createPipeline(channelId: string, topic: string): Promise<PipelineJob> {
  return apiFetch<PipelineJob>('/api/pipeline/create', {
    method: 'POST',
    body: JSON.stringify({ channel_id: channelId, topic }),
  });
}

export async function approvePipeline(pipelineId: string): Promise<void> {
  await apiFetch(`/api/pipeline/${pipelineId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved: true }),
  });
}

export async function runPipeline(pipelineId: string): Promise<void> {
  await apiFetch(`/api/pipeline/${pipelineId}/run`, { method: 'POST' });
}

// Assets

export interface Asset {
  name: string;
  path: string;
  type: string;
  url: string;
}

export async function fetchAssets(): Promise<Asset[]> {
  const data = await apiFetch<Asset[] | { assets: Asset[] }>('/api/assets');
  return Array.isArray(data) ? data : [];
}

// Media generation

export async function generateMedia(
  endpoint: string,
  body: Record<string, string>,
): Promise<unknown> {
  return apiFetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
