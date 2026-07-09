'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useWorkspaceStore } from '@/lib/stores/workspace';
import { useSessionStore } from '@/lib/stores/session';
import { gatewayUrl } from '@/lib/api';

interface FileTreeProps {
  onSelect: (path: string) => void;
}

interface FileEntry {
  name: string;
  path: string;
  isDir: boolean;
  children?: FileEntry[];
}

export function FileTree({ onSelect }: FileTreeProps) {
  const fileTree = useWorkspaceStore((s) => s.fileTree);
  const setFileTree = useWorkspaceStore((s) => s.setFileTree);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; entry: FileEntry | null } | null>(null);
  const [renaming, setRenaming] = useState<string | null>(null);
  const [creating, setCreating] = useState<{ parentPath: string; isDir: boolean } | null>(null);
  const [newName, setNewName] = useState('');
  const newNameRef = useRef<HTMLInputElement>(null);

  const sessions = useSessionStore((s) => s.sessions);

  const activeSessions = Array.from(sessions.values());
  const activeFiles = new Set<string>();
  for (const session of activeSessions) {
    for (const event of session.events) {
      if (event.type === 'tool_call' && (event.tool_name === 'write_file' || event.tool_name === 'edit_file')) {
        const path = (event.tool_args as Record<string, unknown>)?.path;
        if (typeof path === 'string') {
          activeFiles.add(path);
        }
      }
    }
  }

  const loadTree = useCallback(async () => {
    try {
      const resp = await fetch(gatewayUrl('/api/ide/files'));
      const data = await resp.json();
      if (data.status === 'ok') {
        setFileTree(data.files || []);
      }
    } catch {
      setFileTree([]);
    }
  }, [setFileTree]);

  useEffect(() => {
    if (fileTree.length === 0) {
      loadTree();
    }
  }, [fileTree.length, loadTree]);

  const refreshTree = useCallback(async () => {
    try {
      const resp = await fetch(gatewayUrl('/api/ide/files'));
      const data = await resp.json();
      if (data.status === 'ok') {
        setFileTree(data.files || []);
      }
    } catch {
      // keep existing tree
    }
  }, [setFileTree]);

  const toggleDir = (path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const handleContextMenu = (e: React.MouseEvent, entry: FileEntry | null) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, entry });
  };

  const handleCreateFile = async (parentPath: string) => {
    if (!newName.trim()) return;
    const fullPath = parentPath ? `${parentPath}/${newName.trim()}` : newName.trim();
    try {
      await fetch(gatewayUrl('/api/ide/file'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: fullPath, content: '' }),
      });
      setCreating(null);
      setNewName('');
      refreshTree();
    } catch {
      // keep state
    }
  };

  const handleCreateDir = async (parentPath: string) => {
    if (!newName.trim()) return;
    const fullPath = parentPath ? `${parentPath}/${newName.trim()}` : newName.trim();
    try {
      await fetch(gatewayUrl('/api/ide/file'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: `${fullPath}/.keep`, content: '' }),
      });
      setCreating(null);
      setNewName('');
      refreshTree();
    } catch {
      // keep state
    }
  };

  const handleDelete = async (path: string) => {
    if (!confirm(`Delete "${path}"?`)) return;
    try {
      await fetch(gatewayUrl('/api/ide/file'), {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });
      refreshTree();
    } catch {
      // keep state
    }
  };

  const handleContextAction = (action: string) => {
    if (!contextMenu) return;
    const entry = contextMenu.entry;

    if (action === 'copy_path' && entry) {
      navigator.clipboard.writeText(entry.path);
    } else if (action === 'copy_for_agent' && entry) {
      navigator.clipboard.writeText(`File: ${entry.path}\n\nPlease review this file.`);
    } else if (action === 'new_file') {
      const parentPath = entry?.isDir ? entry.path : entry?.path.split('/').slice(0, -1).join('/') || '';
      setCreating({ parentPath, isDir: false });
      setNewName('');
    } else if (action === 'new_folder') {
      const parentPath = entry?.isDir ? entry.path : entry?.path.split('/').slice(0, -1).join('/') || '';
      setCreating({ parentPath, isDir: true });
      setNewName('');
    } else if (action === 'delete' && entry) {
      handleDelete(entry.path);
    }

    setContextMenu(null);
  };

  useEffect(() => {
    if (creating && newNameRef.current) {
      newNameRef.current.focus();
    }
  }, [creating]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const menu = document.getElementById('filetree-context-menu');
      if (menu && menu.contains(e.target as Node)) return;
      setContextMenu(null);
    };
    if (contextMenu) {
      document.addEventListener('mousedown', handleClick);
      return () => document.removeEventListener('mousedown', handleClick);
    }
  }, [contextMenu]);

  const renderEntry = (entry: FileEntry, depth: number = 0) => {
    const isExpanded = expanded.has(entry.path);
    const isActive = activeFiles.has(entry.path);

    return (
      <div key={entry.path}>
        <div
          className="flex items-center gap-1.5 px-2 py-1 text-xs text-[#7a7a8e] hover:bg-[#22222e] hover:text-[#e8e8ec] cursor-pointer transition-colors group"
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
          onClick={() => {
            if (entry.isDir) {
              toggleDir(entry.path);
            } else {
              onSelect(entry.path);
            }
          }}
          onContextMenu={(e) => handleContextMenu(e, entry)}
        >
          <span className="w-4 text-center text-[10px]">
            {entry.isDir ? (isExpanded ? '▾' : '▸') : '·'}
          </span>
          <span className={entry.isDir ? 'text-[#eab308]' : ''}>
            {entry.name}
          </span>
          {isActive && (
            <span className="w-1.5 h-1.5 rounded-full bg-[#22c55e] pulse-dot shrink-0" />
          )}
        </div>
        {creating && creating.parentPath === entry.path && (
          <div style={{ paddingLeft: `${(depth + 1) * 12 + 8}px` }} className="flex items-center gap-1 px-2 py-1">
            <span className="w-4 text-center text-[10px] text-[#7a7a8e]">
              {creating.isDir ? '▸' : '·'}
            </span>
            <input
              ref={newNameRef}
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  creating.isDir ? handleCreateDir(creating.parentPath) : handleCreateFile(creating.parentPath);
                }
                if (e.key === 'Escape') {
                  setCreating(null);
                  setNewName('');
                }
              }}
              onBlur={() => {
                setCreating(null);
                setNewName('');
              }}
              placeholder={creating.isDir ? 'folder name' : 'file name'}
              className="bg-[#0a0a12] border border-[#2a2a36] rounded px-1.5 py-0.5 text-xs text-[#e8e8ec] outline-none focus:border-[#00e5ff] transition-colors flex-1 min-w-0"
            />
          </div>
        )}
        {entry.isDir && isExpanded && entry.children && (
          <div>
            {entry.children.map((child) => renderEntry(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto py-1" onContextMenu={(e) => handleContextMenu(e, null)}>
      {fileTree.length === 0 && (
        <div className="text-xs text-[#555] px-4 py-8 text-center">
          No files found
        </div>
      )}
      {fileTree.map((entry) => renderEntry(entry))}

      {contextMenu && (
        <div
          id="filetree-context-menu"
          className="fixed z-50 bg-[#1a1a22] border border-[#2a2a36] rounded-lg py-1 shadow-xl min-w-[140px]"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() => handleContextAction('new_file')}
            className="w-full px-3 py-1.5 text-xs text-left text-[#e8e8ec] hover:bg-[#22222e] transition-colors"
          >
            New File
          </button>
          <button
            onClick={() => handleContextAction('new_folder')}
            className="w-full px-3 py-1.5 text-xs text-left text-[#e8e8ec] hover:bg-[#22222e] transition-colors"
          >
            New Folder
          </button>
          {contextMenu.entry && (
            <>
              <div className="border-t border-[#2a2a36] my-1" />
              <button
                onClick={() => handleContextAction('copy_path')}
                className="w-full px-3 py-1.5 text-xs text-left text-[#e8e8ec] hover:bg-[#22222e] transition-colors"
              >
                Copy Path
              </button>
              <button
                onClick={() => handleContextAction('copy_for_agent')}
                className="w-full px-3 py-1.5 text-xs text-left text-[#00e5ff] hover:bg-[#22222e] transition-colors"
              >
                Copy for Agent
              </button>
              <div className="border-t border-[#2a2a36] my-1" />
              <button
                onClick={() => handleContextAction('delete')}
                className="w-full px-3 py-1.5 text-xs text-left text-[#ef4444] hover:bg-[#22222e] transition-colors"
              >
                Delete
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
