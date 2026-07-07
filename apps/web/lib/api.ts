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
  const data = await apiFetch<{ status: string; tree: FileEntry[] }>(
    '/api/ide/files',
  );
  return data.tree;
}

export async function sendAgentMessage(
  task: string,
  model: string,
  sessionId: string,
): Promise<Response> {
  return fetch(
    `${BASE_URL}/api/ide/stream?task=${encodeURIComponent(task)}&model=${encodeURIComponent(model)}&session_id=${sessionId}`,
  );
}

export async function approveTool(sessionId: string): Promise<void> {
  await apiFetch('/api/ide/approve', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function rejectTool(
  sessionId: string,
  feedback: string,
): Promise<void> {
  await apiFetch('/api/ide/reject', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, feedback }),
  });
}

interface FileEntry {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileEntry[];
}
