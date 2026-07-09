import { create } from 'zustand';
import type { AgentEvent } from '../types';

interface Session {
  id: string;
  events: AgentEvent[];
  status: 'active' | 'completed' | 'error';
  task: string;
  model: string;
  isGenerating: boolean;
  error: string | null;
}

interface SessionStore {
  sessions: Map<string, Session>;
  activeSessionId: string | null;
  archivedSessions: Array<{ id: string; kind: string; status: string; created_at: string; updated_at: string }>;
  createSession: (task: string) => string;
  setActiveSession: (id: string) => void;
  appendEvent: (sessionId: string, event: AgentEvent) => void;
  setGenerating: (sessionId: string, value: boolean) => void;
  setError: (sessionId: string, error: string | null) => void;
  clearSession: (sessionId: string) => void;
  loadArchivedSessions: (sessions: Array<{ id: string; kind: string; status: string; created_at: string; updated_at: string }>) => void;
  loadSessionMessages: (sessionId: string, messages: Array<{ role: string; content: string; created_at: string }>) => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
  sessions: new Map(),
  activeSessionId: null,
  archivedSessions: [],

  createSession: (task: string) => {
    const id = crypto.randomUUID();
    const session: Session = {
      id,
      events: [],
      status: 'active',
      task,
      model: 'unknown',
      isGenerating: true,
      error: null,
    };
    set((state) => {
      const next = new Map(state.sessions);
      next.set(id, session);
      return { sessions: next, activeSessionId: id };
    });
    return id;
  },

  setActiveSession: (id: string) => {
    set({ activeSessionId: id });
  },

  appendEvent: (sessionId: string, event: AgentEvent) => {
    set((state) => {
      const next = new Map(state.sessions);
      const session = next.get(sessionId);
      if (session) {
        // Update model from event if available
        const model = (event as any).model || session.model;
        next.set(sessionId, { ...session, events: [...session.events, event], model });
      }
      return { sessions: next };
    });
  },

  setGenerating: (sessionId: string, value: boolean) => {
    set((state) => {
      const next = new Map(state.sessions);
      const session = next.get(sessionId);
      if (session) {
        next.set(sessionId, { ...session, isGenerating: value });
      }
      return { sessions: next };
    });
  },

  setError: (sessionId: string, error: string | null) => {
    set((state) => {
      const next = new Map(state.sessions);
      const session = next.get(sessionId);
      if (session) {
        next.set(sessionId, { ...session, error });
      }
      return { sessions: next };
    });
  },

  clearSession: (sessionId: string) => {
    set((state) => {
      const next = new Map(state.sessions);
      const session = next.get(sessionId);
      if (session) {
        next.set(sessionId, {
          ...session,
          events: [],
          status: 'active',
          isGenerating: false,
          error: null,
        });
      }
      return { sessions: next };
    });
  },

  loadArchivedSessions: (sessions) => {
    set({ archivedSessions: sessions });
  },

  loadSessionMessages: (sessionId, messages) => {
    set((state) => {
      const next = new Map(state.sessions);
      const existing = next.get(sessionId);
      const events: AgentEvent[] = messages.map((m) => ({
        type: m.role === 'user' ? 'user_message' : 'text',
        content: m.content,
      }));
      next.set(sessionId, {
        id: sessionId,
        events,
        status: 'completed',
        task: events[0]?.content?.slice(0, 100) || 'Past session',
        model: existing?.model || 'unknown',
        isGenerating: false,
        error: null,
      });
      return { sessions: next, activeSessionId: sessionId };
    });
  },
}));
