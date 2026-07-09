'use client';

import { useState, useEffect, useCallback } from 'react';
import { useWorkspaceStore } from '@/lib/stores/workspace';
import { gatewayUrl } from '@/lib/api';

interface WorkspaceModalProps {
  open: boolean;
  onClose: () => void;
}

interface BrowseItem {
  name: string;
  path: string;
  isDir: boolean;
}

export function WorkspaceModal({ open, onClose }: WorkspaceModalProps) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [browsePath, setBrowsePath] = useState('/');
  const [browseItems, setBrowseItems] = useState<BrowseItem[]>([]);
  const [browseLoading, setBrowseLoading] = useState(false);
  const [showBrowser, setShowBrowser] = useState(false);

  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const setFileTree = useWorkspaceStore((s) => s.setFileTree);
  const workspaceRoot = useWorkspaceStore((s) => s.workspaceRoot);

  useEffect(() => {
    if (open) {
      setInput(workspaceRoot || '');
      setError('');
      setBrowsePath('/');
      setShowBrowser(false);
    }
  }, [open, workspaceRoot]);

  const loadBrowse = useCallback(async (path: string) => {
    setBrowseLoading(true);
    try {
      const res = await fetch(gatewayUrl(`/api/orchestrator/workspace/browse?path=${encodeURIComponent(path)}`));
      const data = await res.json();
      setBrowsePath(data.path || path);
      setBrowseItems(data.items || []);
    } catch {
      setBrowseItems([]);
    }
    setBrowseLoading(false);
  }, []);

  useEffect(() => {
    if (showBrowser) {
      loadBrowse(browsePath);
    }
  }, [showBrowser, browsePath, loadBrowse]);

  const handleSet = useCallback(async () => {
    const path = input.trim();
    if (!path) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch(gatewayUrl('/api/ide/workspace'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });
      const data = await res.json();
      if (data.status !== 'ok') {
        setError(data.detail || 'Failed to set workspace');
        setLoading(false);
        return;
      }

      setWorkspace(data.workspace_root);
      localStorage.setItem('spark_workspace_root', data.workspace_root);

      const treeRes = await fetch(gatewayUrl('/api/ide/files'));
      const treeData = await treeRes.json();
      if (treeData.status === 'ok') {
        setFileTree(treeData.files || []);
      }

      setLoading(false);
      onClose();
    } catch {
      setError('Connection failed');
      setLoading(false);
    }
  }, [input, setWorkspace, setFileTree, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl max-w-lg w-full p-6 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-sm font-mono text-[#e8e8ec] mb-4">Select Workspace</h2>

        {/* Path Input */}
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSet(); if (e.key === 'Escape') onClose(); }}
            placeholder="/path/to/workspace"
            className="flex-1 bg-[#0a0a12] border border-[#2a2a36] rounded-lg px-3 py-2 text-sm text-[#e8e8ec] outline-none focus:border-[#00e5ff] transition-colors font-mono"
            autoFocus
          />
          <button
            onClick={() => setShowBrowser(!showBrowser)}
            className="px-3 py-2 text-xs bg-[#22222e] border border-[#2a2a36] rounded-lg text-[#7a7a8e] hover:text-[#e8e8ec] hover:border-[#3a3a4a] transition-colors"
            title="Browse folders"
          >
            Browse
          </button>
        </div>

        {/* Folder Browser */}
        {showBrowser && (
          <div className="mb-3 border border-[#2a2a36] rounded-lg bg-[#0a0a12] max-h-48 overflow-y-auto">
            {/* Breadcrumb */}
            <div className="px-3 py-2 border-b border-[#2a2a36] flex items-center gap-1 text-[10px] font-mono text-[#7a7a8e]">
              {browsePath.split('/').filter(Boolean).map((part, i, arr) => (
                <span key={i} className="flex items-center gap-1">
                  {i > 0 && <span>/</span>}
                  <button
                    onClick={() => setBrowsePath('/' + arr.slice(0, i + 1).join('/'))}
                    className="hover:text-[#00e5ff] transition-colors"
                  >
                    {part}
                  </button>
                </span>
              ))}
            </div>

            {/* Items */}
            {browseLoading ? (
              <div className="px-3 py-4 text-xs text-[#555] text-center">Loading...</div>
            ) : (
              <div className="py-1">
                {browsePath !== '/' && (
                  <button
                    onClick={() => {
                      const parent = browsePath.split('/').slice(0, -1).join('/') || '/';
                      setBrowsePath(parent);
                    }}
                    className="w-full px-3 py-1.5 text-xs text-left text-[#7a7a8e] hover:bg-[#22222e] hover:text-[#e8e8ec] transition-colors flex items-center gap-2"
                  >
                    <span className="w-4 text-center">..</span>
                    <span className="text-[#eab308]">Parent</span>
                  </button>
                )}
                {browseItems.filter(i => i.isDir).map((item) => (
                  <button
                    key={item.path}
                    onClick={() => {
                      setBrowsePath(item.path);
                      setInput(item.path);
                    }}
                    className="w-full px-3 py-1.5 text-xs text-left text-[#7a7a8e] hover:bg-[#22222e] hover:text-[#e8e8ec] transition-colors flex items-center gap-2"
                  >
                    <span className="w-4 text-center text-[#eab308]">▸</span>
                    <span>{item.name}</span>
                  </button>
                ))}
                {browseItems.filter(i => i.isDir).length === 0 && (
                  <div className="px-3 py-2 text-xs text-[#555]">No folders</div>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <p className="text-xs text-[#ef4444] mb-3">{error}</p>
        )}
        <div className="flex justify-end gap-2 mt-auto">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-xs text-[#7a7a8e] hover:text-[#e8e8ec] transition-colors rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSet}
            disabled={loading || !input.trim()}
            className="px-3 py-1.5 text-xs bg-[#00e5ff] text-black rounded-lg font-mono disabled:opacity-40 hover:brightness-110 transition-all"
          >
            {loading ? 'Setting...' : 'Set Workspace'}
          </button>
        </div>
      </div>
    </div>
  );
}
