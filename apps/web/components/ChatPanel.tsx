'use client';

import { useState, useRef, useEffect } from 'react';
import { ApprovalCard } from './ApprovalCard';
import type { AgentEvent } from '@/lib/types';

interface ChatPanelProps {
  events: AgentEvent[];
  onSend: (message: string) => void;
  onApprove: (toolCallId: string) => void;
  onReject: (toolCallId: string, feedback: string) => void;
  isGenerating?: boolean;
}

export function ChatPanel({ events, onSend, onApprove, onReject, isGenerating }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 100) + 'px';
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim()) {
      onSend(input.trim());
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#1a1a22]">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 && (
          <p className="text-xs text-[#7a7a8e] text-center mt-8">
            Send a message to start chatting with the agent.
          </p>
        )}
        {events.map((event, i) => (
          <div key={i} className="text-xs">
            {event.type === 'text' && (
              <div className="bg-[#22222e] rounded-lg p-3">
                <div className="text-[#00e5ff] font-mono text-[10px] uppercase mb-1">Agent</div>
                <div className="whitespace-pre-wrap text-[#e8e8ec]">{event.content}</div>
              </div>
            )}
            {event.type === 'tool_call' && (
              <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg p-2">
                <span className="text-[#8b5cf6] font-mono">{event.tool_name}</span>
                {event.tool_args && (
                  <pre className="text-[#7a7a8e] mt-1 overflow-hidden text-[10px]">
                    {JSON.stringify(event.tool_args, null, 2).slice(0, 200)}
                  </pre>
                )}
              </div>
            )}
            {event.type === 'tool_result' && (
              <div className="bg-[#0a0a12] rounded-lg p-2 font-mono text-[10px] text-[#aaa] overflow-hidden max-h-32">
                {typeof event.tool_result === 'string'
                  ? event.tool_result.slice(0, 500)
                  : JSON.stringify(event.tool_result).slice(0, 500)}
              </div>
            )}
            {event.type === 'error' && (
              <div className="bg-[rgba(239,68,68,0.1)] border border-[#ef4444] rounded-lg p-2 text-[#ef4444]">
                {event.error}
              </div>
            )}
            {event.type === 'state_change' && (
              <div className="text-[#7a7a8e] font-mono text-[10px]">
                State: {event.state}
              </div>
            )}
            {(event.type === 'awaiting_file_write' || event.type === 'awaiting_command_run') && (
              <ApprovalCard event={event} onApprove={onApprove} onReject={onReject} />
            )}
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="border-t border-[#2a2a36] p-3">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type a message..."
            rows={1}
            className="flex-1 bg-[#0a0a12] border border-[#2a2a36] rounded-lg px-3 py-2 text-sm text-[#e8e8ec] resize-none outline-none focus:border-[#00e5ff] transition-colors max-h-[100px]"
          />
          <button
            onClick={handleSend}
            disabled={isGenerating || !input.trim()}
            className="w-9 h-9 rounded-lg bg-[#00e5ff] text-black flex items-center justify-center disabled:opacity-40 hover:brightness-110 transition-all shrink-0"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
