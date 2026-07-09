'use client';

import { useState } from 'react';
import { ApprovalCard } from './ApprovalCard';
import type { AgentEvent } from '@/lib/types';

interface ToolCallBlockProps {
  event: AgentEvent;
  toolResult?: AgentEvent;
  onApprove?: (toolCallId: string) => void;
  onReject?: (toolCallId: string, feedback: string) => void;
}

export function ToolCallBlock({ event, toolResult, onApprove, onReject }: ToolCallBlockProps) {
  const [expanded, setExpanded] = useState(false);

  const isApproval = event.type === 'awaiting_file_write' || event.type === 'awaiting_command_run';

  if (isApproval) {
    return (
      <ApprovalCard
        event={event}
        onApprove={onApprove!}
        onReject={onReject!}
      />
    );
  }

  const toolName = event.tool_name || 'unknown';
  const hasResult = !!toolResult;
  const isError = toolResult?.is_error;

  const dotColor = hasResult
    ? isError ? 'bg-[#ef4444]' : 'bg-[#22c55e]'
    : 'bg-[#3b82f6] pulse-dot';

  const argsStr = event.tool_args
    ? JSON.stringify(event.tool_args, null, 2)
    : null;

  const resultStr = toolResult
    ? typeof toolResult.tool_result === 'string'
      ? toolResult.tool_result
      : JSON.stringify(toolResult.tool_result, null, 2)
    : null;

  const truncatedResult = resultStr && resultStr.length > 500;

  return (
    <div className="rounded-lg border border-[#2a2a36] bg-[#1a1a22] overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[#22222e] transition-colors text-left"
      >
        <span className={`w-2 h-2 rounded-full shrink-0 ${dotColor}`} />
        <span className="text-[#8b5cf6] font-mono text-xs">{toolName}</span>
        {hasResult && (
          <span className={`ml-auto text-[10px] font-mono ${isError ? 'text-[#ef4444]' : 'text-[#22c55e]'}`}>
            {isError ? 'failed' : 'done'}
          </span>
        )}
        {!hasResult && (
          <span className="ml-auto text-[10px] font-mono text-[#3b82f6]">running</span>
        )}
        <span className="text-[#555] text-[10px] ml-1">{expanded ? '▾' : '▸'}</span>
      </button>

      {expanded && (
        <div className="border-t border-[#2a2a36]">
          {argsStr && (
            <div className="px-3 py-2">
              <div className="text-[10px] uppercase tracking-wider text-[#7a7a8e] font-mono mb-1">args</div>
              <pre className="text-[10px] font-mono text-[#aaa] bg-[#0a0a12] rounded p-2 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                {argsStr}
              </pre>
            </div>
          )}

          {resultStr && (
            <div className="px-3 py-2 border-t border-[#2a2a36]">
              <div className="text-[10px] uppercase tracking-wider text-[#7a7a8e] font-mono mb-1">result</div>
              <pre className={`text-[10px] font-mono rounded p-2 overflow-x-auto whitespace-pre-wrap ${
                isError
                  ? 'bg-[rgba(239,68,68,0.1)] text-[#ef4444]'
                  : 'bg-[#0a0a12] text-[#aaa]'
              } ${truncatedResult ? 'max-h-32 overflow-y-auto' : ''}`}>
                {truncatedResult ? resultStr.slice(0, 500) : resultStr}
              </pre>
              {truncatedResult && (
                <div className="text-[10px] text-[#555] mt-1 font-mono">
                  ... {resultStr.length} chars total
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
