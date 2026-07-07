/**
 * API client for Spark V2 backend.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

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

export async function sendAgentMessage(
  task: string,
  model: string,
  sessionId: string,
): Promise<Response> {
  return fetch(`${BASE_URL}/api/orchestrator/code/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task, model, session_id: sessionId }),
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

interface FileEntry {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileEntry[];
}
