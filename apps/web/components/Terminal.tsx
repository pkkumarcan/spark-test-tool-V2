'use client';

import { useEffect, useRef } from 'react';
import type { AgentEvent } from '@/lib/types';

interface TerminalProps {
  events: AgentEvent[];
  onToggle?: () => void;
}

export function Terminal({ events, onToggle }: TerminalProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="bg-[#0a0a12] h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#2a2a36] shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[#7a7a8e]">Terminal</span>
          <span className="text-[10px] text-[#555]">
            {events.length} entries
          </span>
        </div>
        {onToggle && (
          <button
            onClick={onToggle}
            className="text-[10px] text-[#555] hover:text-[#aaa] transition-colors"
          >
            ▾
          </button>
        )}
      </div>
      <div
        ref={contentRef}
        className="flex-1 overflow-y-auto p-3 font-mono text-xs text-[#aaa] whitespace-pre-wrap break-word"
      >
        {events.length === 0 && (
          <div className="text-[#555]">Terminal output will appear here...</div>
        )}
        {events.map((event, i) => {
          const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
          const isError =
            event.type === 'tool_result' &&
            typeof event.tool_result === 'string' &&
            (event.tool_result.includes('Error') || event.tool_result.includes('error'));

          return (
            <div
              key={i}
              className={isError ? 'text-[#ef4444]' : ''}
            >
              <span className="text-[#555]">[{timestamp}]</span>{' '}
              {event.type === 'tool_result' && (
                <span>{typeof event.tool_result === 'string' ? event.tool_result : JSON.stringify(event.tool_result)}</span>
              )}
              {event.type === 'terminal_log' && (
                <span>{event.content}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
