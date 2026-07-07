'use client';

import { useEffect, useState, useCallback } from 'react';

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
  const [tree, setTree] = useState<FileEntry[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const loadTree = useCallback(async () => {
    try {
      const resp = await fetch('/api/ide/files');
      const data = await resp.json();
      if (data.status === 'ok') {
        setTree(data.tree || []);
      }
    } catch {
      setTree([]);
    }
  }, []);

  useEffect(() => {
    loadTree();
  }, [loadTree]);

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

  const renderEntry = (entry: FileEntry, depth: number = 0) => {
    const isExpanded = expanded.has(entry.path);

    return (
      <div key={entry.path}>
        <div
          className="flex items-center gap-1.5 px-2 py-1 text-xs text-[#7a7a8e] hover:bg-[#22222e] hover:text-[#e8e8ec] cursor-pointer transition-colors"
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
          onClick={() => {
            if (entry.isDir) {
              toggleDir(entry.path);
            } else {
              onSelect(entry.path);
            }
          }}
        >
          <span className="w-4 text-center text-[10px]">
            {entry.isDir ? (isExpanded ? '▾' : '▸') : '·'}
          </span>
          <span className={entry.isDir ? 'text-[#eab308]' : ''}>
            {entry.name}
          </span>
        </div>
        {entry.isDir && isExpanded && entry.children && (
          <div>
            {entry.children.map((child) => renderEntry(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto py-1">
      {tree.length === 0 && (
        <div className="text-xs text-[#555] px-4 py-8 text-center">
          No files found
        </div>
      )}
      {tree.map((entry) => renderEntry(entry))}
    </div>
  );
}
