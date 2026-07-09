'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { MonacoEditor } from '@/components/MonacoEditor';
import { Terminal } from '@/components/Terminal';
import { FileTree } from '@/components/FileTree';
import { SessionManager } from '@/components/SessionManager';
import { WorkspaceModal } from '@/components/WorkspaceModal';
import { TaskPipeline } from '@/components/TaskPipeline';
import { ChatMessage } from '@/components/ChatMessage';
import { HtmlPreview } from '@/components/HtmlPreview';
import { MemoryEditor } from '@/components/MemoryEditor';
import { RAGPanel } from '@/components/RAGPanel';
import { useAgentSSE } from '@/lib/sse';
import { useSessionStore } from '@/lib/stores/session';
import { useWorkspaceStore } from '@/lib/stores/workspace';
import { useUIStore } from '@/lib/stores/ui';
import { gatewayUrl, readFile, fetchModels, type ModelInfo } from '@/lib/api';

function getFileName(path: string): string {
  return path.split('/').pop() ?? path;
}

function isHtmlFile(path: string): boolean {
  return /\.(html?|htm)$/i.test(path);
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

interface Attachment {
  id: string;
  name: string;
  type: 'image' | 'file';
  base64: string;
  preview?: string;
  size: number;
}

export default function IDEPage() {
  const selectedFile = useWorkspaceStore((s) => s.selectedFile);
  const setSelectedFile = useWorkspaceStore((s) => s.setSelectedFile);
  const workspaceRoot = useWorkspaceStore((s) => s.workspaceRoot);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const setFileTree = useWorkspaceStore((s) => s.setFileTree);
  const terminalOpen = useUIStore((s) => s.terminalOpen);
  const toggleTerminal = useUIStore((s) => s.toggleTerminal);
  const sidebarTab = useUIStore((s) => s.sidebarTab);
  const setSidebarTab = useUIStore((s) => s.setSidebarTab);

  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const sessions = useSessionStore((s) => s.sessions);
  const setActiveSession = useSessionStore((s) => s.setActiveSession);
  const createSession = useSessionStore((s) => s.createSession);

  const [chatInput, setChatInput] = useState('');
  const [rightPanelView, setRightPanelView] = useState<'chat' | 'pipeline' | 'knowledge'>('chat');
  const [workspaceModalOpen, setWorkspaceModalOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewContainerRef = useRef<HTMLDivElement>(null);

  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState('qwen3:8b');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [htmlContent, setHtmlContent] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [memoryOpen, setMemoryOpen] = useState(false);
  const loadArchivedSessions = useSessionStore((s) => s.loadArchivedSessions);

  // Load workspace
  useEffect(() => {
    const saved = localStorage.getItem('spark_workspace_root');
    if (saved) {
      setWorkspace(saved);
      fetch(gatewayUrl('/api/ide/workspace'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: saved }),
      }).then(async () => {
        const res = await fetch(gatewayUrl('/api/ide/files'));
        const data = await res.json();
        if (data.status === 'ok') setFileTree(data.files || []);
      }).catch(() => {});
    } else {
      setWorkspaceModalOpen(true);
    }
  }, [setWorkspace, setFileTree]);

  // Load models
  useEffect(() => {
    fetchModels().then((data) => {
      setModels(data.models);
      if (data.default) setSelectedModel(data.default);
    }).catch(() => {});
  }, []);

  // Load archived sessions
  useEffect(() => {
    fetch(gatewayUrl('/api/orchestrator/sessions?limit=20'))
      .then((r) => r.json())
      .then((data) => {
        if (data.sessions) loadArchivedSessions(data.sessions);
      })
      .catch(() => {});
  }, [loadArchivedSessions]);

  // Persist model selection
  useEffect(() => {
    const saved = localStorage.getItem('spark_model');
    if (saved) setSelectedModel(saved);
  }, []);

  // Load HTML content when file changes
  useEffect(() => {
    if (selectedFile && isHtmlFile(selectedFile)) {
      readFile(selectedFile).then((content) => {
        setHtmlContent(content);
        setShowPreview(true);
      }).catch(() => {});
    } else {
      setHtmlContent('');
      setShowPreview(false);
    }
  }, [selectedFile]);

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    localStorage.setItem('spark_model', model);
  };

  const { events, send, stopSession, approve, reject, isGenerating, error } = useAgentSSE('/api/orchestrator/code/stream');

  const terminalEvents = events.filter(
    (e) => e.type === 'terminal_log' || e.type === 'tool_result'
  );

  const handleFileSelect = useCallback((path: string) => {
    setSelectedFile(path);
  }, [setSelectedFile]);

  // Handle image paste (Ctrl+V)
  const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    const items = Array.from(e.clipboardData.items);
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (!file) continue;
        const base64 = await fileToBase64(file);
        const preview = URL.createObjectURL(file);
        setAttachments((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            name: file.name || `pasted-image-${Date.now()}.png`,
            type: 'image',
            base64,
            preview,
            size: file.size,
          },
        ]);
      }
    }
  }, []);

  // Handle file upload
  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    for (const file of files) {
      const base64 = await fileToBase64(file);
      const isImage = file.type.startsWith('image/');
      const attachment: Attachment = {
        id: crypto.randomUUID(),
        name: file.name,
        type: isImage ? 'image' : 'file',
        base64,
        size: file.size,
      };
      if (isImage) {
        attachment.preview = URL.createObjectURL(file);
      }
      setAttachments((prev) => [...prev, attachment]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  const removeAttachment = useCallback((id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
  }, []);

  // Capture preview screenshot
  const handleCapturePreview = useCallback(async () => {
    if (!previewContainerRef.current) return;

    setIsCapturing(true);
    try {
      const container = previewContainerRef.current;
      const iframe = container.querySelector('iframe');
      if (!iframe) return;

      // Try to access iframe content (same-origin via blob URL)
      let canvas: HTMLCanvasElement;
      try {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
        if (iframeDoc) {
          const html2canvas = (await import('html2canvas')).default;
          canvas = await html2canvas(iframeDoc.documentElement, {
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            scale: 1,
          });
        } else {
          throw new Error('Cannot access iframe');
        }
      } catch {
        // Fallback: capture the container
        const html2canvas = (await import('html2canvas')).default;
        canvas = await html2canvas(container, {
          useCORS: true,
          allowTaint: true,
          scale: 1,
        });
      }

      const base64 = canvas.toDataURL('image/png').split(',')[1];
      setAttachments((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          name: 'preview-screenshot.png',
          type: 'image',
          base64,
          preview: canvas.toDataURL('image/png'),
          size: Math.round(base64.length * 0.75),
        },
      ]);
    } catch (err) {
      console.error('Screenshot capture failed:', err);
    } finally {
      setIsCapturing(false);
    }
  }, []);

  const handleSend = useCallback(() => {
    if (!chatInput.trim() && attachments.length === 0) return;

    let sid = activeSessionId;
    if (!sid || !sessions.has(sid)) {
      sid = createSession(chatInput.trim() || 'File analysis');
    }

    const images = attachments
      .filter((a) => a.type === 'image')
      .map((a) => a.base64);

    const fileContext = attachments
      .filter((a) => a.type === 'file')
      .map((a) => `\n\n[Attached file: ${a.name} (${(a.size / 1024).toFixed(1)}KB)]`)
      .join('');

    const fullMessage = chatInput.trim() + fileContext;

    send(sid, fullMessage || 'Analyze the attached files', images.length > 0 ? images : undefined);
    setChatInput('');
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [chatInput, attachments, send, activeSessionId, sessions, createSession]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [chatInput]);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [events]);

  const handleCopyLast = useCallback(() => {
    const lastText = [...events].reverse().find((e) => e.type === 'text');
    if (lastText?.content) {
      navigator.clipboard.writeText(lastText.content);
    }
  }, [events]);

  const needsApproval = events.some(
    (e) =>
      e.type === 'awaiting_file_write' || e.type === 'awaiting_command_run'
  );
  const statusLabel = needsApproval ? 'needs approval' : isGenerating ? 'thinking' : 'idle';
  const statusColor = needsApproval
    ? 'bg-[#eab308]'
    : isGenerating
      ? 'bg-[#00e5ff]'
      : 'bg-[#22c55e]';

  const sessionTabs = Array.from(sessions.values()).reverse();

  const handleCloseTab = (sid: string) => {
    const idx = sessionTabs.findIndex((s) => s.id === sid);
    const remaining = sessionTabs.filter((s) => s.id !== sid);
    if (remaining.length === 0) {
      setActiveSession('');
    } else if (sid === activeSessionId) {
      const nextIdx = Math.min(idx, remaining.length - 1);
      setActiveSession(remaining[nextIdx].id);
    }
  };

  return (
    <div className="flex h-screen bg-[#0f0f14] text-[#e8e8ec] overflow-hidden">
      {/* Left Sidebar */}
      <div className="w-64 min-w-64 border-r border-[#2a2a36] flex flex-col shrink-0">
        {workspaceRoot && (
          <button
            onClick={() => setWorkspaceModalOpen(true)}
            className="px-4 py-2 border-b border-[#2a2a36] text-left text-[10px] font-mono text-[#7a7a8e] hover:text-[#00e5ff] hover:bg-[#1a1a22] transition-colors truncate"
          >
            {workspaceRoot.split('/').pop() || workspaceRoot}
          </button>
        )}
        <div className="px-4 py-3 border-b border-[#2a2a36] flex items-center gap-2">
          <button
            onClick={() => setSidebarTab('explorer')}
            className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-mono rounded transition-colors ${
              sidebarTab === 'explorer'
                ? 'bg-[#22222e] text-[#e8e8ec]'
                : 'text-[#555] hover:text-[#7a7a8e]'
            }`}
          >
            Explorer
          </button>
          <button
            onClick={() => setSidebarTab('sessions')}
            className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-mono rounded transition-colors ${
              sidebarTab === 'sessions'
                ? 'bg-[#22222e] text-[#e8e8ec]'
                : 'text-[#555] hover:text-[#7a7a8e]'
            }`}
          >
            Sessions
          </button>
        </div>
        {sidebarTab === 'explorer' && <FileTree onSelect={handleFileSelect} />}
        {sidebarTab === 'sessions' && <SessionManager />}

        {/* Memory Button */}
        <div className="px-4 py-2 border-t border-[#2a2a36]">
          <button
            onClick={() => setMemoryOpen(true)}
            className="w-full px-2 py-1.5 text-[10px] uppercase tracking-wider font-mono rounded text-[#7a7a8e] hover:text-[#00e5ff] hover:bg-[#22222e] transition-colors flex items-center gap-2"
          >
            <span>🧠</span>
            <span>Agent Memory</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Session Tabs */}
        {sessionTabs.length > 0 && (
          <div className="shrink-0 flex items-center border-b border-[#2a2a36] bg-[#0a0a12] overflow-x-auto">
            {sessionTabs.map((tab) => (
              <div
                key={tab.id}
                onClick={() => setActiveSession(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs cursor-pointer border-r border-[#2a2a36] shrink-0 max-w-[180px] ${
                  tab.id === activeSessionId
                    ? 'bg-[#0f0f14] text-[#e8e8ec] border-t-2 border-t-[#00e5ff]'
                    : 'text-[#555] hover:bg-[#1a1a22] hover:text-[#aaa]'
                }`}
              >
                {tab.isGenerating && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#22c55e] pulse-dot shrink-0" />
                )}
                <span className="truncate">
                  {tab.task.length > 20 ? tab.task.slice(0, 20) + '…' : tab.task}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCloseTab(tab.id);
                  }}
                  className="ml-1 text-[#555] hover:text-[#ef4444] transition-colors shrink-0"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* File Tab Bar */}
        {selectedFile && (
          <div className="shrink-0 flex items-center border-b border-[#2a2a36] bg-[#0a0a12]">
            <div className="flex items-center gap-1 px-3 py-2 bg-[#0f0f14] border-r border-[#2a2a36] text-xs">
              <span className="text-[#e8e8ec] font-mono">
                {getFileName(selectedFile)}
              </span>
              <button
                onClick={() => setSelectedFile(null)}
                className="ml-2 text-[#555] hover:text-[#ef4444] transition-colors"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Editor + Preview Area */}
        <div className="flex-1 flex min-h-0">
          {/* Editor */}
          <div className={`${showPreview ? 'w-1/2' : 'w-full'} min-h-0 border-r border-[#2a2a36]`}>
            <MonacoEditor file={selectedFile} />
          </div>

          {/* Preview Panel */}
          {showPreview && (
            <div className="w-1/2 flex flex-col min-h-0">
              {/* Preview Header */}
              <div className="shrink-0 flex items-center justify-between px-3 py-2 bg-[#0a0a12] border-b border-[#2a2a36]">
                <span className="text-[10px] uppercase tracking-wider text-[#7a7a8e] font-mono">
                  Live Preview
                </span>
                <button
                  onClick={handleCapturePreview}
                  disabled={isCapturing}
                  className="px-2 py-1 text-[10px] font-mono rounded bg-[#00e5ff] text-black hover:brightness-110 disabled:opacity-50 transition-all"
                >
                  {isCapturing ? 'Capturing...' : '📸 Capture & Send'}
                </button>
              </div>
              {/* Preview Content */}
              <div ref={previewContainerRef} className="flex-1 min-h-0 bg-white">
                <HtmlPreview
                  htmlContent={htmlContent}
                  onCapture={(base64) => {
                    setAttachments((prev) => [
                      ...prev,
                      {
                        id: crypto.randomUUID(),
                        name: 'preview-screenshot.png',
                        type: 'image',
                        base64,
                        size: Math.round(base64.length * 0.75),
                      },
                    ]);
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Terminal Panel */}
        {terminalOpen && (
          <div className="shrink-0 border-t border-[#2a2a36] max-h-48">
            <Terminal
              events={terminalEvents}
              onToggle={toggleTerminal}
            />
          </div>
        )}

        {/* Terminal Toggle */}
        {!terminalOpen && (
          <button
            onClick={toggleTerminal}
            className="shrink-0 border-t border-[#2a2a36] px-4 py-1.5 text-left text-xs text-[#7a7a8e] hover:text-[#aaa] hover:bg-[#1a1a22] transition-colors"
          >
            ▸ Terminal ({terminalEvents.length})
          </button>
        )}

        {/* Chat Input Bar */}
        <div className="shrink-0 border-t border-[#2a2a36] p-3">
          {/* Model Selector */}
          <div className="max-w-3xl mx-auto mb-2 flex items-center gap-2">
            <label className="text-[10px] uppercase tracking-wider text-[#7a7a8e] font-mono">Model:</label>
            <select
              value={selectedModel}
              onChange={(e) => handleModelChange(e.target.value)}
              className="bg-[#1a1a22] border border-[#2a2a36] rounded px-2 py-1 text-xs text-[#e8e8ec] font-mono focus:border-[#00e5ff] outline-none"
            >
              {models.length > 0 ? (
                models.map((m) => (
                  <option key={m.name} value={m.name}>{m.name}</option>
                ))
              ) : (
                <>
                  <option value="qwen3:8b">qwen3:8b</option>
                  <option value="gemma4:12b-it-qat">gemma4:12b-it-qat</option>
                  <option value="llama3.2-vision:11b">llama3.2-vision:11b</option>
                </>
              )}
            </select>
            <span className="text-[10px] text-[#555] font-mono">
              {models.length > 0 ? `${models.length} models` : 'loading...'}
            </span>
          </div>

          {/* Attachments Preview */}
          {attachments.length > 0 && (
            <div className="max-w-3xl mx-auto mb-2 flex flex-wrap gap-2">
              {attachments.map((att) => (
                <div key={att.id} className="relative group">
                  {att.preview ? (
                    <img
                      src={att.preview}
                      alt={att.name}
                      className="w-16 h-16 object-cover rounded border border-[#2a2a36]"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded border border-[#2a2a36] bg-[#1a1a22] flex items-center justify-center">
                      <span className="text-[8px] text-[#7a7a8e] text-center px-1 truncate max-w-[60px]">
                        {att.name.split('.').pop()?.toUpperCase()}
                      </span>
                    </div>
                  )}
                  <button
                    onClick={() => removeAttachment(att.id)}
                    className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#ef4444] text-white text-[8px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    ×
                  </button>
                  <div className="text-[8px] text-[#555] text-center truncate w-16 mt-0.5">
                    {att.name.length > 10 ? att.name.slice(0, 8) + '…' : att.name}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Input Area */}
          <div className="max-w-3xl mx-auto flex items-end gap-3">
            {/* File Upload Button */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,.pdf,.txt,.md,.json,.csv,.py,.js,.ts,.html,.css,.xml,.yaml,.yml"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-10 h-10 rounded-lg bg-[#1a1a22] border border-[#2a2a36] text-[#7a7a8e] flex items-center justify-center hover:text-[#e8e8ec] hover:border-[#3a3a4a] transition-all shrink-0"
              title="Attach files (images, PDFs, etc.)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>

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
                onPaste={handlePaste}
                placeholder="Ask Spark to code, search, or run commands... (Ctrl+V to paste images)"
                rows={1}
                className="w-full bg-transparent text-[#e8e8ec] resize-none outline-none text-sm leading-relaxed max-h-[120px]"
              />
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {isGenerating && activeSessionId && (
                <button
                  onClick={() => stopSession(activeSessionId)}
                  className="w-10 h-10 rounded-lg bg-[rgba(239,68,68,0.15)] border border-[#ef4444] text-[#ef4444] flex items-center justify-center hover:bg-[rgba(239,68,68,0.25)] transition-all"
                  title="Stop generation"
                >
                  ⏹
                </button>
              )}
              {!isGenerating && events.some((e) => e.type === 'text') && (
                <button
                  onClick={handleCopyLast}
                  className="w-10 h-10 rounded-lg bg-[#1a1a22] border border-[#2a2a36] text-[#7a7a8e] flex items-center justify-center hover:text-[#e8e8ec] hover:border-[#3a3a4a] transition-all"
                  title="Copy last response"
                >
                  ⧉
                </button>
              )}
              <button
                onClick={handleSend}
                disabled={isGenerating || (!chatInput.trim() && attachments.length === 0)}
                className="w-10 h-10 rounded-lg bg-[#00e5ff] text-black flex items-center justify-center disabled:opacity-40 hover:brightness-110 transition-all"
              >
                ↑
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Panel Sidebar */}
      <div className="w-80 min-w-80 border-l border-[#2a2a36] flex flex-col bg-[#1a1a22] shrink-0 h-full overflow-hidden">
        <div className="px-4 py-3 border-b border-[#2a2a36] flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setRightPanelView('chat')}
              className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-mono rounded transition-colors ${
                rightPanelView === 'chat'
                  ? 'bg-[#22222e] text-[#e8e8ec]'
                  : 'text-[#555] hover:text-[#7a7a8e]'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setRightPanelView('pipeline')}
              className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-mono rounded transition-colors ${
                rightPanelView === 'pipeline'
                  ? 'bg-[#22222e] text-[#e8e8ec]'
                  : 'text-[#555] hover:text-[#7a7a8e]'
              }`}
            >
              Pipeline
            </button>
            <button
              onClick={() => setRightPanelView('knowledge')}
              className={`px-2 py-0.5 text-[10px] uppercase tracking-wider font-mono rounded transition-colors ${
                rightPanelView === 'knowledge'
                  ? 'bg-[#22222e] text-[#e8e8ec]'
                  : 'text-[#555] hover:text-[#7a7a8e]'
              }`}
            >
              Knowledge
            </button>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${statusColor} ${isGenerating ? 'pulse-dot' : ''}`} />
            <span className="text-[10px] uppercase tracking-wider text-[#7a7a8e] font-mono">
              {statusLabel}
            </span>
          </div>
        </div>
        {rightPanelView === 'chat' ? (
          <div ref={chatScrollRef} className="flex-1 overflow-y-auto py-2 space-y-0.5">
            {events.length === 0 && !error && (
              <p className="text-[11px] text-[#444] text-center mt-8">
                No events yet. Send a message to start.
              </p>
            )}
            {error && (
              <div className="mx-3 bg-[rgba(239,68,68,0.1)] border border-[#ef4444] rounded-lg p-2 text-[11px] text-[#ef4444]">
                Connection error: {error}
              </div>
            )}
            {events.map((event, i) => (
              <ChatMessage
                key={i}
                event={event}
                onApprove={approve}
                onReject={reject}
              />
            ))}
          </div>
        ) : rightPanelView === 'pipeline' ? (
          <div className="flex-1 overflow-hidden">
            <TaskPipeline events={events} onApprove={approve} onReject={reject} />
          </div>
        ) : (
          <div className="flex-1 overflow-hidden">
            <RAGPanel />
          </div>
        )}
      </div>
      <WorkspaceModal open={workspaceModalOpen} onClose={() => setWorkspaceModalOpen(false)} />
      <MemoryEditor open={memoryOpen} onClose={() => setMemoryOpen(false)} />
    </div>
  );
}
