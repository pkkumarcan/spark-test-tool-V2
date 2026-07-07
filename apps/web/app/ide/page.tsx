'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { MonacoEditor } from '@/components/MonacoEditor';
import { Terminal } from '@/components/Terminal';
import { FileTree } from '@/components/FileTree';
import { ApprovalCard } from '@/components/ApprovalCard';
import { useAgentSSE } from '@/lib/sse';

export default function IDEPage() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState('');
  const [terminalOpen, setTerminalOpen] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { events, send, approve, reject, isGenerating } = useAgentSSE('/api/orchestrator/code/stream');

  const terminalEvents = events.filter(
    (e) => e.type === 'terminal_log' || e.type === 'tool_result'
  );

  const handleFileSelect = useCallback((path: string) => {
    setSelectedFile(path);
  }, []);

  const handleSend = useCallback(() => {
    if (chatInput.trim()) {
      send(chatInput.trim());
      setChatInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  }, [chatInput, send]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [chatInput]);

  return (
    <div className="flex h-screen bg-[#0f0f14] text-[#e8e8ec] overflow-hidden">
      {/* File Tree Sidebar */}
      <div className="w-64 min-w-64 border-r border-[#2a2a36] flex flex-col shrink-0">
        <div className="px-4 py-3 border-b border-[#2a2a36]">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#7a7a8e]">
            Explorer
          </h3>
        </div>
        <FileTree onSelect={handleFileSelect} />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Editor Area */}
        <div className="flex-1 min-h-0">
          <MonacoEditor file={selectedFile} />
        </div>

        {/* Terminal Panel */}
        {terminalOpen && (
          <div className="shrink-0 border-t border-[#2a2a36] max-h-48">
            <Terminal
              events={terminalEvents}
              onToggle={() => setTerminalOpen(false)}
            />
          </div>
        )}

        {/* Terminal Toggle (when closed) */}
        {!terminalOpen && (
          <button
            onClick={() => setTerminalOpen(true)}
            className="shrink-0 border-t border-[#2a2a36] px-4 py-1.5 text-left text-xs text-[#7a7a8e] hover:text-[#aaa] hover:bg-[#1a1a22] transition-colors"
          >
            ▸ Terminal ({terminalEvents.length})
          </button>
        )}

        {/* Chat Input Bar */}
        <div className="shrink-0 border-t border-[#2a2a36] p-3">
          <div className="max-w-3xl mx-auto flex items-end gap-3">
            <div className="flex-1 bg-[#1a1a22] border border-[#2a2a36] rounded-xl px-4 py-2.5 focus-within:border-[#00e5ff] transition-colors">
              <textarea
                ref={textareaRef}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask Spark to code, search, or run commands..."
                rows={1}
                className="w-full bg-transparent text-[#e8e8ec] resize-none outline-none text-sm leading-relaxed max-h-[120px]"
              />
            </div>
            <button
              onClick={handleSend}
              disabled={isGenerating || !chatInput.trim()}
              className="w-10 h-10 rounded-lg bg-[#00e5ff] text-black flex items-center justify-center disabled:opacity-40 hover:brightness-110 transition-all shrink-0"
            >
              {isGenerating ? '⏹' : '↑'}
            </button>
          </div>
        </div>
      </div>

      {/* Chat Panel Sidebar */}
      <div className="w-80 min-w-80 border-l border-[#2a2a36] flex flex-col bg-[#1a1a22] shrink-0">
        <div className="px-4 py-3 border-b border-[#2a2a36]">
          <h3 className="text-sm font-semibold">Agent Chat</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {events.length === 0 && (
            <p className="text-xs text-[#7a7a8e] text-center mt-8">
              No events yet. Send a message to start.
            </p>
          )}
          {events.map((event, i) => (
            <div key={i} className="text-xs">
              {event.type === 'text' && (
                <div className="bg-[#22222e] rounded-lg p-3">
                  <div className="text-[#00e5ff] font-mono text-[10px] uppercase mb-1">Agent</div>
                  <div className="whitespace-pre-wrap">{event.content}</div>
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
                <ApprovalCard
                  event={event}
                  onApprove={approve}
                  onReject={reject}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
