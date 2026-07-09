'use client';

import { useEffect, useCallback, useRef } from 'react';
import { useSessionStore } from './stores/session';
import { gatewayUrl } from './api';
import type { AgentEvent } from './types';

interface UseAgentSEReturn {
  events: AgentEvent[];
  send: (sessionId: string, message: string, images?: string[]) => void;
  stopSession: (sessionId: string) => void;
  approve: (toolCallId: string) => void;
  reject: (toolCallId: string, feedback: string) => void;
  isGenerating: boolean;
  error: string | null;
}

export function useAgentSSE(
  endpoint: string,
  sessionId?: string,
): UseAgentSEReturn {
  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const appendEvent = useSessionStore((s) => s.appendEvent);
  const setGenerating = useSessionStore((s) => s.setGenerating);
  const setError = useSessionStore((s) => s.setError);
  const sessions = useSessionStore((s) => s.sessions);

  const currentSessionId = sessionId ?? activeSessionId;
  const session = currentSessionId ? sessions.get(currentSessionId) : undefined;
  const events = session?.events ?? [];
  const isGenerating = session?.isGenerating ?? false;
  const error = session?.error ?? null;

  const controllersRef = useRef<Map<string, AbortController>>(new Map());

  const stopSession = useCallback(
    (sessionId: string) => {
      const controller = controllersRef.current.get(sessionId);
      if (controller) {
        controller.abort();
        controllersRef.current.delete(sessionId);
      }
      setGenerating(sessionId, false);
    },
    [setGenerating],
  );

  const send = useCallback(
    (sessionId: string, message: string, images?: string[]) => {
      const existing = controllersRef.current.get(sessionId);
      if (existing) {
        existing.abort();
      }

      const controller = new AbortController();
      controllersRef.current.set(sessionId, controller);

      setGenerating(sessionId, true);
      setError(sessionId, null);

      const url = gatewayUrl(endpoint);

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: message, session_id: sessionId, images }),
        signal: controller.signal,
      })
        .then((resp) => {
          if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
          const reader = resp.body!.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          const processStream = (): Promise<void> =>
            reader.read().then(({ done, value }) => {
              if (done) {
                controllersRef.current.delete(sessionId);
                setGenerating(sessionId, false);
                return;
              }

              buffer += decoder.decode(value, { stream: true });
              const blocks = buffer.split('\n\n');
              buffer = blocks.pop() ?? '';

              for (const block of blocks) {
                let eventType = '';
                let dataStr = '';
                for (const line of block.split('\n')) {
                  if (line.startsWith('event: ')) eventType = line.slice(7).trim();
                  if (line.startsWith('data: ')) dataStr = line.slice(6);
                }
                if (!dataStr) continue;

                try {
                  const parsed = JSON.parse(dataStr) as AgentEvent;
                  parsed.type = parsed.type || eventType;
                  appendEvent(sessionId, parsed);
                } catch {
                  // skip malformed events
                }
              }

              return processStream();
            });

          return processStream();
        })
        .catch((err) => {
          controllersRef.current.delete(sessionId);
          if (err.name !== 'AbortError') {
            setError(sessionId, err.message);
            setGenerating(sessionId, false);
          }
        });
    },
    [endpoint, appendEvent, setGenerating, setError],
  );

  const approve = useCallback(async (toolCallId: string) => {
    await fetch(gatewayUrl('/api/orchestrator/code/approve'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_call_id: toolCallId }),
    });
  }, []);

  const reject = useCallback(async (toolCallId: string, feedback: string) => {
    await fetch(gatewayUrl('/api/orchestrator/code/reject'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_call_id: toolCallId, feedback }),
    });
  }, []);

  useEffect(() => {
    return () => {
      controllersRef.current.forEach((c) => c.abort());
      controllersRef.current.clear();
    };
  }, []);

  return { events, send, stopSession, approve, reject, isGenerating, error };
}
