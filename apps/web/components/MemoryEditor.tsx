'use client';

import { useState, useEffect, useCallback } from 'react';
import { gatewayUrl } from '@/lib/api';

interface MemoryEditorProps {
  open: boolean;
  onClose: () => void;
}

export function MemoryEditor({ open, onClose }: MemoryEditorProps) {
  const [memory, setMemory] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (open) {
      setLoading(true);
      setError('');
      fetch(gatewayUrl('/api/orchestrator/code/memory'))
        .then((r) => r.json())
        .then((data) => {
          setMemory(data.memory || '');
          setLoading(false);
        })
        .catch(() => {
          setError('Failed to load memory');
          setLoading(false);
        });
    }
  }, [open]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setError('');
    try {
      const res = await fetch(gatewayUrl('/api/orchestrator/code/memory'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      } else {
        setError('Failed to save');
      }
    } catch {
      setError('Connection failed');
    }
    setSaving(false);
  }, [memory]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl max-w-2xl w-full p-6 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-mono text-[#e8e8ec]">Agent Memory</h2>
            <p className="text-[10px] text-[#555] mt-1">Long-term context the agent remembers across sessions</p>
          </div>
          <button
            onClick={onClose}
            className="text-[#555] hover:text-[#e8e8ec] transition-colors"
          >
            ×
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex items-center justify-center text-xs text-[#555]">Loading...</div>
        ) : (
          <>
            <textarea
              value={memory}
              onChange={(e) => setMemory(e.target.value)}
              className="flex-1 bg-[#0a0a12] border border-[#2a2a36] rounded-lg p-3 text-xs text-[#e8e8ec] font-mono resize-none outline-none focus:border-[#00e5ff] transition-colors min-h-[300px]"
              placeholder="# Agent Memory&#10;&#10;Write long-term context here: project info, hardware specs, business rules..."
            />
            <div className="flex items-center justify-between mt-3">
              <span className="text-[10px] text-[#555] font-mono">
                {memory.length} chars · {memory.split('\n').length} lines
              </span>
              {error && <span className="text-[10px] text-[#ef4444]">{error}</span>}
              {saved && <span className="text-[10px] text-[#22c55e]">Saved!</span>}
            </div>
          </>
        )}

        <div className="flex justify-end gap-2 mt-4">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-xs text-[#7a7a8e] hover:text-[#e8e8ec] transition-colors rounded-lg"
          >
            Close
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="px-3 py-1.5 text-xs bg-[#00e5ff] text-black rounded-lg font-mono disabled:opacity-40 hover:brightness-110 transition-all"
          >
            {saving ? 'Saving...' : 'Save Memory'}
          </button>
        </div>
      </div>
    </div>
  );
}
