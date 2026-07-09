'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useSessionStore } from '@/lib/stores/session';
import { useAgentSSE } from '@/lib/sse';
import { gatewayUrl } from '@/lib/api';

function timeGroup(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays <= 7) return 'Previous 7 Days';
  return 'Older';
}

function shortTitle(task: string): string {
  const clean = task.replace(/[#*`>\-\n]/g, ' ').trim();
  return clean.length > 40 ? clean.slice(0, 40) + '…' : clean || 'Untitled';
}

function relativeTime(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  const days = Math.floor(hrs / 24);
  return `${days}d`;
}

export function SessionManager() {
  const sessions = useSessionStore((s) => s.sessions);
  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const setActiveSession = useSessionStore((s) => s.setActiveSession);
  const createSession = useSessionStore((s) => s.createSession);
  const archivedSessions = useSessionStore((s) => s.archivedSessions);
  const loadSessionMessages = useSessionStore((s) => s.loadSessionMessages);

  const { send, stopSession } = useAgentSSE('/api/orchestrator/code/stream');

  const [creating, setCreating] = useState(false);
  const [newTask, setNewTask] = useState('');
  const [loadingHistory, setLoadingHistory] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (creating && inputRef.current) {
      inputRef.current.focus();
    }
  }, [creating]);

  const handleCreate = () => {
    const task = newTask.trim();
    if (!task) return;
    const sid = createSession(task);
    send(sid, task);
    setNewTask('');
    setCreating(false);
  };

  const loadSession = useCallback(async (sessionId: string) => {
    setLoadingHistory(sessionId);
    try {
      const res = await fetch(gatewayUrl(`/api/orchestrator/sessions/${sessionId}/messages`));
      const data = await res.json();
      if (data.messages) {
        loadSessionMessages(sessionId, data.messages);
      }
    } catch {
      // ignore
    }
    setLoadingHistory(null);
  }, [loadSessionMessages]);

  const sessionList = Array.from(sessions.values()).reverse();

  const grouped = archivedSessions.reduce<Record<string, typeof archivedSessions>>((acc, s) => {
    const group = timeGroup(s.updated_at);
    if (!acc[group]) acc[group] = [];
    acc[group].push(s);
    return acc;
  }, {});

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="px-3 py-2 border-b border-[#2a2a36] flex items-center justify-between">
        <h3 className="text-[10px] font-semibold uppercase tracking-wider text-[#555]">
          Sessions
        </h3>
        <button
          onClick={() => setCreating(!creating)}
          className="w-5 h-5 flex items-center justify-center rounded text-[#7a7a8e] hover:text-[#00e5ff] hover:bg-[#22222e] transition-colors text-xs"
        >
          +
        </button>
      </div>

      {creating && (
        <div className="px-2 py-1.5 border-b border-[#2a2a36]">
          <input
            ref={inputRef}
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleCreate();
              if (e.key === 'Escape') {
                setCreating(false);
                setNewTask('');
              }
            }}
            onBlur={() => {
              if (!newTask.trim()) {
                setCreating(false);
              }
            }}
            placeholder="Describe the task..."
            className="w-full bg-[#0a0a12] border border-[#2a2a36] rounded px-2 py-1 text-[11px] text-[#e8e8ec] placeholder-[#555] outline-none focus:border-[#00e5ff] transition-colors"
          />
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {sessionList.length > 0 && (
          <div className="px-3 py-1 text-[9px] uppercase tracking-wider text-[#444] font-mono">
            Active
          </div>
        )}
        {sessionList.map((session) => {
          const isActive = session.id === activeSessionId;
          const dotColor = session.isGenerating
            ? 'bg-[#22c55e]'
            : session.status === 'completed'
              ? 'bg-[#3b82f6]'
              : session.status === 'error'
                ? 'bg-[#ef4444]'
                : 'bg-[#555]';

          return (
            <div
              key={session.id}
              onClick={() => setActiveSession(session.id)}
              className={`flex items-center gap-2 px-3 py-1.5 cursor-pointer transition-colors ${
                isActive
                  ? 'bg-[#22222e] text-[#e8e8ec]'
                  : 'text-[#7a7a8e] hover:bg-[#1a1a22] hover:text-[#aaa]'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  session.isGenerating ? 'pulse-dot' : ''
                } ${dotColor}`}
              />
              <span className="text-[11px] truncate flex-1 min-w-0">
                {shortTitle(session.task)}
              </span>
              {session.model !== 'unknown' && (
                <span className="text-[8px] text-[#444] font-mono shrink-0">
                  {session.model.split(':')[0]}
                </span>
              )}
              {session.isGenerating && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    stopSession(session.id);
                  }}
                  className="text-[#ef4444] hover:text-[#ff6b6b] transition-colors text-[9px] shrink-0"
                >
                  ■
                </button>
              )}
            </div>
          );
        })}

        {Object.entries(grouped).map(([group, items]) => (
          <div key={group}>
            <div className="px-3 py-1 mt-1 text-[9px] uppercase tracking-wider text-[#444] font-mono border-t border-[#1a1a22]">
              {group}
            </div>
            {items.map((session) => {
              const isLoaded = sessions.has(session.id);
              const isLoading = loadingHistory === session.id;

              return (
                <div
                  key={session.id}
                  onClick={() => {
                    if (!isLoaded) loadSession(session.id);
                    else setActiveSession(session.id);
                  }}
                  className={`flex items-center gap-2 px-3 py-1.5 cursor-pointer transition-colors ${
                    session.id === activeSessionId
                      ? 'bg-[#22222e] text-[#e8e8ec]'
                      : 'text-[#7a7a8e] hover:bg-[#1a1a22] hover:text-[#aaa]'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    session.status === 'active' ? 'bg-[#22c55e]' : 'bg-[#444]'
                  }`} />
                  <span className="text-[11px] truncate flex-1 min-w-0">
                    {shortTitle(session.id)}
                  </span>
                  <span className="text-[9px] text-[#444] shrink-0">
                    {isLoading ? '...' : relativeTime(session.updated_at)}
                  </span>
                </div>
              );
            })}
          </div>
        ))}

        {sessionList.length === 0 && archivedSessions.length === 0 && !creating && (
          <div className="text-[11px] text-[#444] px-4 py-8 text-center">
            No sessions yet
          </div>
        )}
      </div>
    </div>
  );
}
