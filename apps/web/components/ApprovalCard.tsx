'use client';

import { useState } from 'react';
import { DiffViewer } from './DiffViewer';
import type { AgentEvent } from '@/lib/types';

interface ApprovalCardProps {
  event: AgentEvent;
  onApprove: (toolCallId: string) => void;
  onReject: (toolCallId: string, feedback: string) => void;
}

export function ApprovalCard({ event, onApprove, onReject }: ApprovalCardProps) {
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected'>('pending');
  const [feedback, setFeedback] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  const toolCallId = (event as any).tool_call_id;
  const isCommand = event.type === 'awaiting_command_run';
  const label = isCommand ? 'COMMAND RUN' : 'FILE WRITE';
  const icon = isCommand ? '⚡' : '📝';
  const path = (event as any).path || '';

  const handleApprove = () => {
    setStatus('approved');
    onApprove(toolCallId);
  };

  const handleReject = () => {
    if (!showRejectInput) {
      setShowRejectInput(true);
      return;
    }
    setStatus('rejected');
    onReject(toolCallId, feedback || 'Rejected by user.');
  };

  const handleRejectConfirm = () => {
    setStatus('rejected');
    onReject(toolCallId, feedback || 'Rejected by user.');
  };

  return (
    <div className="rounded-lg border border-[#2a2a36] bg-[#1a1a22] overflow-hidden my-2">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 bg-[#22222e] border-b border-[#2a2a36]">
        <span className="text-sm">{icon}</span>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-[#00e5ff]">
          {label}
        </span>
        {path && (
          <span className="text-[11px] font-mono text-[#7a7a8e] truncate ml-1 max-w-[260px]">
            {path}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-3 max-h-[300px] overflow-y-auto">
        {isCommand ? (
          <pre className="text-xs font-mono text-[#e8e8ec] bg-[#0a0a12] rounded p-2 whitespace-pre-wrap">
            {event.command || ''}
          </pre>
        ) : event.diff ? (
          <DiffViewer diff={event.diff} />
        ) : event.content ? (
          <pre className="text-xs font-mono text-[#aaa] whitespace-pre-wrap">{event.content}</pre>
        ) : null}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 px-3 py-2 border-t border-[#2a2a36]">
        {status === 'pending' ? (
          <>
            <button
              onClick={handleApprove}
              className="px-4 py-1.5 text-xs font-semibold rounded bg-[#22c55e] text-black hover:brightness-110 transition-all"
            >
              Approve
            </button>
            {!showRejectInput ? (
              <button
                onClick={handleReject}
                className="px-4 py-1.5 text-xs font-semibold rounded border border-[#ef4444] text-[#ef4444] hover:bg-[rgba(239,68,68,0.1)] transition-all"
              >
                Reject
              </button>
            ) : (
              <div className="flex items-center gap-2 flex-1">
                <input
                  type="text"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Rejection reason..."
                  className="flex-1 px-3 py-1.5 text-xs bg-[#0a0a12] border border-[#2a2a36] rounded text-[#e8e8ec] outline-none focus:border-[#ef4444]"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRejectConfirm();
                  }}
                />
                <button
                  onClick={handleRejectConfirm}
                  className="px-3 py-1.5 text-xs font-semibold rounded bg-[#ef4444] text-white hover:brightness-110 transition-all"
                >
                  Confirm
                </button>
              </div>
            )}
          </>
        ) : (
          <span
            className={`text-xs font-semibold ${
              status === 'approved' ? 'text-[#22c55e]' : 'text-[#ef4444]'
            }`}
          >
            {status === 'approved' ? '✓ Approved' : '✗ Rejected'}
          </span>
        )}
      </div>
    </div>
  );
}
