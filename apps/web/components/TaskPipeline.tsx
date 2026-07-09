'use client';

import { useRef, useEffect, useMemo } from 'react';
import { ToolCallBlock } from './ToolCallBlock';
import type { AgentEvent, AgentStateType } from '@/lib/types';

interface TaskPipelineProps {
  events: AgentEvent[];
  onApprove?: (toolCallId: string) => void;
  onReject?: (toolCallId: string, feedback: string) => void;
}

interface Phase {
  state: AgentStateType | null;
  label: string;
  events: AgentEvent[];
  isCurrent: boolean;
  isCompleted: boolean;
  isFailed: boolean;
}

const STATE_LABELS: Record<string, string> = {
  planning: 'Planning',
  tool_call: 'Tool Call',
  sandbox_exec: 'Execute',
  verify: 'Verify',
  approval_pending: 'Awaiting Approval',
  apply: 'Apply',
  done: 'Done',
  failed: 'Failed',
};

function groupEventsIntoPhases(events: AgentEvent[]): Phase[] {
  const phases: Phase[] = [];
  let current: Phase | null = null;

  for (const event of events) {
    if (event.type === 'state_change' && event.state) {
      current = {
        state: event.state,
        label: STATE_LABELS[event.state] || event.state,
        events: [],
        isCurrent: false,
        isCompleted: event.state === 'done',
        isFailed: event.state === 'failed',
      };
      phases.push(current);
    } else {
      if (!current) {
        current = {
          state: null,
          label: 'Initializing',
          events: [],
          isCurrent: false,
          isCompleted: false,
          isFailed: false,
        };
        phases.push(current);
      }
      current.events.push(event);
    }
  }

  for (let i = phases.length - 1; i >= 0; i--) {
    if (!phases[i].isCompleted && !phases[i].isFailed) {
      phases[i].isCurrent = true;
      break;
    }
  }

  return phases;
}

function findToolResult(events: AgentEvent[], toolName: string, index: number): AgentEvent | undefined {
  for (let i = index + 1; i < events.length; i++) {
    if (events[i].type === 'tool_result') {
      return events[i];
    }
    if (events[i].type === 'tool_call') break;
  }
  return undefined;
}

export function TaskPipeline({ events, onApprove, onReject }: TaskPipelineProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  const phases = useMemo(() => groupEventsIntoPhases(events), [events]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [phases.length]);

  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-[#7a7a8e]">
        No activity yet.
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-4 py-3">
      <div className="relative">
        <div className="absolute left-[5px] top-0 bottom-0 w-px bg-[#2a2a36]" />

        {phases.map((phase, pi) => (
          <div key={pi} className="relative pl-6 pb-4">
            <div
              className={`absolute left-0 top-0 w-[11px] h-[11px] rounded-full border-2 border-[#0f0f14] z-10 ${
                phase.isCompleted
                  ? 'bg-[#22c55e]'
                  : phase.isFailed
                    ? 'bg-[#ef4444]'
                    : phase.isCurrent
                      ? 'bg-[#00e5ff] pulse-dot'
                      : 'bg-[#555]'
              }`}
              style={{ marginTop: '2px' }}
            >
              {(phase.isCompleted || phase.isFailed) && (
                <span className="absolute inset-0 flex items-center justify-center text-[7px] text-white font-bold leading-none">
                  {phase.isCompleted ? '✓' : '✗'}
                </span>
              )}
            </div>

            <div className="flex items-baseline gap-2">
              <span className={`text-xs font-semibold ${
                phase.isCurrent
                  ? 'text-[#00e5ff]'
                  : phase.isCompleted
                    ? 'text-[#e8e8ec]'
                    : phase.isFailed
                      ? 'text-[#ef4444]'
                      : 'text-[#555]'
              }`}>
                {phase.label}
              </span>
              {phase.isCurrent && (
                <span className="text-[10px] text-[#00e5ff] font-mono">● active</span>
              )}
            </div>

            {phase.events.length > 0 && (
              <div className="mt-2 space-y-2">
                {phase.events.map((event, ei) => {
                  if (event.type === 'text') {
                    return (
                      <div key={ei} className="bg-[#22222e] rounded-lg p-2 text-xs text-[#e8e8ec] whitespace-pre-wrap">
                        {event.content}
                      </div>
                    );
                  }

                  if (event.type === 'tool_call') {
                    const toolResult = findToolResult(phase.events, event.tool_name || '', ei);
                    return (
                      <ToolCallBlock
                        key={ei}
                        event={event}
                        toolResult={toolResult}
                        onApprove={onApprove}
                        onReject={onReject}
                      />
                    );
                  }

                  if (event.type === 'tool_result') {
                    const prevEvent = ei > 0 ? phase.events[ei - 1] : null;
                    if (prevEvent?.type === 'tool_call') return null;
                    return (
                      <div key={ei} className="bg-[#0a0a12] rounded-lg p-2 font-mono text-[10px] text-[#aaa] overflow-hidden max-h-24">
                        {typeof event.tool_result === 'string'
                          ? event.tool_result.slice(0, 500)
                          : JSON.stringify(event.tool_result).slice(0, 500)}
                      </div>
                    );
                  }

                  if (event.type === 'error') {
                    return (
                      <div key={ei} className="bg-[rgba(239,68,68,0.1)] border border-[#ef4444] rounded-lg p-2 text-xs text-[#ef4444]">
                        {event.error}
                      </div>
                    );
                  }

                  if (event.type === 'awaiting_file_write' || event.type === 'awaiting_command_run') {
                    return (
                      <ToolCallBlock
                        key={ei}
                        event={event}
                        onApprove={onApprove}
                        onReject={onReject}
                      />
                    );
                  }

                  return null;
                })}
              </div>
            )}
          </div>
        ))}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
