'use client';

import { useState, useEffect, useCallback } from 'react';
import type { Job, JobStatus } from '@/lib/types';

interface PipelineDashboardProps {
  refreshInterval?: number;
}

const STATUS_COLORS: Record<JobStatus, string> = {
  pending: 'text-[#f59e0b]',
  running: 'text-[#3b82f6]',
  completed: 'text-[#22c55e]',
  failed: 'text-[#ef4444]',
  cancelled: 'text-[#7a7a8e]',
};

const STATUS_BG: Record<JobStatus, string> = {
  pending: 'bg-[rgba(245,158,11,0.1)]',
  running: 'bg-[rgba(59,130,246,0.1)]',
  completed: 'bg-[rgba(34,197,94,0.1)]',
  failed: 'bg-[rgba(239,68,68,0.1)]',
  cancelled: 'bg-[rgba(122,122,142,0.1)]',
};

export function PipelineDashboard({ refreshInterval = 5000 }: PipelineDashboardProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [statusFilter, setStatusFilter] = useState<JobStatus | ''>('');
  const [kindFilter, setKindFilter] = useState('');

  const fetchJobs = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (kindFilter) params.set('kind', kindFilter);
      params.set('limit', '50');

      const r = await fetch(`/api/jobs?${params}`);
      if (r.ok) {
        const data = await r.json();
        setJobs(data);
      }
    } catch {
      // silent
    }
  }, [statusFilter, kindFilter]);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchJobs, refreshInterval]);

  const stats = {
    total: jobs.length,
    pending: jobs.filter((j) => j.status === 'pending').length,
    running: jobs.filter((j) => j.status === 'running').length,
    completed: jobs.filter((j) => j.status === 'completed').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
  };

  return (
    <div className="space-y-4">
      {/* Stats Row */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'Total', value: stats.total, color: 'text-[#e8e8ec]' },
          { label: 'Pending', value: stats.pending, color: 'text-[#f59e0b]' },
          { label: 'Running', value: stats.running, color: 'text-[#3b82f6]' },
          { label: 'Completed', value: stats.completed, color: 'text-[#22c55e]' },
          { label: 'Failed', value: stats.failed, color: 'text-[#ef4444]' },
        ].map((s) => (
          <div key={s.label} className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg p-3 text-center">
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-[10px] text-[#7a7a8e] uppercase mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as JobStatus | '')}
          className="bg-[#1a1a22] border border-[#2a2a36] rounded px-3 py-1.5 text-xs text-[#e8e8ec] outline-none"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          value={kindFilter}
          onChange={(e) => setKindFilter(e.target.value)}
          className="bg-[#1a1a22] border border-[#2a2a36] rounded px-3 py-1.5 text-xs text-[#e8e8ec] outline-none"
        >
          <option value="">All kinds</option>
          <option value="image">Image</option>
          <option value="video">Video</option>
          <option value="audio">Audio</option>
          <option value="3d">3D</option>
          <option value="music">Music</option>
          <option value="tts">TTS</option>
          <option value="stt">STT</option>
          <option value="meme">Meme</option>
          <option value="postprocess">Postprocess</option>
          <option value="extraction">Extraction</option>
        </select>
        <button
          onClick={fetchJobs}
          className="px-3 py-1.5 text-xs bg-[#22222e] border border-[#2a2a36] rounded hover:bg-[#2a2a36] transition-colors text-[#aaa]"
        >
          Refresh
        </button>
      </div>

      {/* Jobs Table */}
      <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[#2a2a36] text-[#7a7a8e] uppercase text-[10px]">
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Kind</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">GPU</th>
              <th className="px-4 py-2 text-left">Created</th>
              <th className="px-4 py-2 text-left">Error</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} className="border-b border-[#2a2a36] hover:bg-[#22222e]">
                <td className="px-4 py-2 font-mono text-[10px] text-[#aaa]">{job.id.slice(0, 8)}</td>
                <td className="px-4 py-2">{job.kind}</td>
                <td className="px-4 py-2">
                  <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${STATUS_COLORS[job.status]} ${STATUS_BG[job.status]}`}>
                    {job.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-[#7a7a8e]">{job.gpu_node ?? '—'}</td>
                <td className="px-4 py-2 text-[#7a7a8e]">{new Date(job.created_at).toLocaleTimeString()}</td>
                <td className="px-4 py-2 text-[#ef4444] max-w-[200px] truncate">{job.error ?? ''}</td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-[#7a7a8e]">No jobs found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
