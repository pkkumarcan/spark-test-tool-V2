'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import type { AgentEvent } from './types';

interface UseAgentSEReturn {
  events: AgentEvent[];
  send: (message: string) => void;
  approve: (toolCallId: string) => void;
  reject: (toolCallId: string, feedback: string) => void;
  isGenerating: boolean;
  error: string | null;
}

export function useAgentSSE(endpoint: string): UseAgentSEReturn {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    (message: string) => {
      abortRef.current?.abort();
      setEvents([]);
      setError(null);
      setIsGenerating(true);

      const controller = new AbortController();
      abortRef.current = controller;

      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: message }),
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
                setIsGenerating(false);
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
                  setEvents((prev) => [...prev, parsed]);
                } catch {
                  // skip malformed events
                }
              }

              return processStream();
            });

          return processStream();
        })
        .catch((err) => {
          if (err.name !== 'AbortError') {
            setError(err.message);
            setIsGenerating(false);
          }
        });
    },
    [endpoint],
  );

  const approve = useCallback(async (toolCallId: string) => {
    await fetch('/api/orchestrator/code/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_call_id: toolCallId }),
    });
  }, []);

  const reject = useCallback(async (toolCallId: string, feedback: string) => {
    await fetch('/api/orchestrator/code/reject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_call_id: toolCallId, feedback }),
    });
  }, []);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  return { events, send, approve, reject, isGenerating, error };
}
