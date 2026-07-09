'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { gatewayUrl } from '@/lib/api';

interface RAGSource {
  id: string;
  name: string;
  chunks: number;
  sample: string;
}

export function RAGPanel() {
  const [sources, setSources] = useState<RAGSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [query, setQuery] = useState('');
  const [queryResults, setQueryResults] = useState<Array<{ text: string; score: number; source: string }>>([]);
  const [querying, setQuerying] = useState(false);
  const [status, setStatus] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadSources = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(gatewayUrl('/api/rag/sources'));
      const data = await res.json();
      setSources(data.sources || []);
    } catch {
      setSources([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadSources();
  }, [loadSources]);

  const ingestText = useCallback(async (text: string, filename: string) => {
    setUploading(true);
    setStatus(`Ingesting ${filename}...`);
    try {
      const res = await fetch(gatewayUrl('/api/rag/ingest'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          metadata: { source_file: filename },
        }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        setStatus(`Ingested ${data.chunks_ingested} chunks from ${filename}`);
        loadSources();
      } else {
        setStatus(`Error: ${data.reason || 'unknown'}`);
      }
    } catch {
      setStatus('Upload failed');
    }
    setUploading(false);
    setTimeout(() => setStatus(''), 3000);
  }, [loadSources]);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    for (const file of Array.from(files)) {
      const text = await file.text();
      await ingestText(text, file.name);
    }
  }, [ingestText]);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      await handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragOver(false), []);

  const handleQuery = useCallback(async () => {
    if (!query.trim()) return;
    setQuerying(true);
    try {
      const res = await fetch(gatewayUrl('/api/rag/query'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim(), limit: 5 }),
      });
      const data = await res.json();
      setQueryResults(data.hits || []);
    } catch {
      setQueryResults([]);
    }
    setQuerying(false);
  }, [query]);

  const handleClearAll = useCallback(async () => {
    if (!confirm('Clear all RAG data? This cannot be undone.')) return;
    await fetch(gatewayUrl('/api/rag/clear-all'), { method: 'POST' });
    setSources([]);
    setStatus('All data cleared');
    setTimeout(() => setStatus(''), 3000);
  }, []);

  const totalChunks = sources.reduce((sum, s) => sum + s.chunks, 0);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 border-b border-[#2a2a36] flex items-center justify-between">
        <div>
          <h3 className="text-[10px] font-semibold uppercase tracking-wider text-[#555]">
            Knowledge Base
          </h3>
          <p className="text-[9px] text-[#444] mt-0.5">
            {sources.length} docs · {totalChunks} chunks
          </p>
        </div>
        <button
          onClick={handleClearAll}
          className="text-[9px] text-[#555] hover:text-[#ef4444] transition-colors font-mono"
        >
          clear
        </button>
      </div>

      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`mx-3 mt-2 mb-1 border-2 border-dashed rounded-lg px-3 py-4 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-[#00e5ff] bg-[rgba(0,229,255,0.05)]'
            : 'border-[#2a2a36] hover:border-[#3a3a4a] hover:bg-[#1a1a22]'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt,.md,.pdf,.json,.csv,.py,.js,.ts,.html,.css"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="hidden"
        />
        <div className="text-[11px] text-[#7a7a8e]">
          {uploading ? (
            <span className="text-[#00e5ff]">Uploading...</span>
          ) : (
            <>
              <span className="text-[#555]">Drop files or click to upload</span>
              <br />
              <span className="text-[9px] text-[#444]">PDF, TXT, MD, JSON, code files</span>
            </>
          )}
        </div>
      </div>

      {/* Query */}
      <div className="px-3 py-1.5">
        <div className="flex gap-1.5">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            placeholder="Search knowledge base..."
            className="flex-1 bg-[#0a0a12] border border-[#2a2a36] rounded px-2 py-1 text-[11px] text-[#e8e8ec] placeholder-[#444] outline-none focus:border-[#00e5ff] transition-colors"
          />
          <button
            onClick={handleQuery}
            disabled={querying || !query.trim()}
            className="px-2 py-1 text-[10px] font-mono rounded bg-[#22222e] text-[#7a7a8e] hover:text-[#e8e8ec] disabled:opacity-40 transition-colors"
          >
            {querying ? '...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Query Results */}
      {queryResults.length > 0 && (
        <div className="px-3 py-1 space-y-1">
          <div className="text-[9px] uppercase tracking-wider text-[#444] font-mono">
            Results ({queryResults.length})
          </div>
          {queryResults.map((hit, i) => (
            <div key={i} className="bg-[#0a0a12] border border-[#2a2a36] rounded px-2 py-1.5">
              <div className="flex items-center gap-1.5 mb-0.5">
                <span className="text-[9px] font-mono text-[#00e5ff]">
                  {(hit.score * 100).toFixed(0)}%
                </span>
                <span className="text-[9px] text-[#444] truncate">{hit.source}</span>
              </div>
              <p className="text-[10px] text-[#aaa] leading-relaxed line-clamp-3">
                {hit.text}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Status */}
      {status && (
        <div className="px-3 py-1">
          <div className="text-[10px] text-[#00e5ff] font-mono">{status}</div>
        </div>
      )}

      {/* Document List */}
      <div className="flex-1 overflow-y-auto px-3 py-1">
        {loading ? (
          <div className="text-[10px] text-[#444] text-center py-4">Loading...</div>
        ) : sources.length === 0 ? (
          <div className="text-[10px] text-[#444] text-center py-4">
            No documents ingested yet
          </div>
        ) : (
          <div className="space-y-1">
            {sources.map((src) => (
              <div
                key={src.id}
                className="bg-[#0a0a12] border border-[#2a2a36] rounded px-2 py-1.5"
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] text-[#e8e8ec] truncate flex-1">
                    {src.name}
                  </span>
                  <span className="text-[9px] text-[#444] font-mono shrink-0">
                    {src.chunks} chunks
                  </span>
                </div>
                {src.sample && (
                  <p className="text-[9px] text-[#555] mt-0.5 line-clamp-2">
                    {src.sample}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
