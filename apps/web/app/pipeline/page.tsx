'use client';

import { useState, useEffect, useCallback } from 'react';
import { listPipelines, approvePipeline, runPipeline, type PipelineJob } from '@/lib/api';

export default function PipelinePage() {
  const [jobs, setJobs] = useState<PipelineJob[]>([]);
  const [channelFilter, setChannelFilter] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchJobs = useCallback(async () => {
    try { setJobs(await listPipelines()); } catch {}
  }, [channelFilter]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const handleApprove = async (pipelineId: string) => {
    setLoading(true);
    try { await approvePipeline(pipelineId); fetchJobs(); } finally { setLoading(false); }
  };

  const handleRun = async (pipelineId: string) => {
    setLoading(true);
    try { await runPipeline(pipelineId); fetchJobs(); } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#00e5ff]">Pipeline Dashboard</h1>
          <p className="text-[#7a7a8e] text-sm mt-1">Content generation pipeline management</p>
        </div>
        <div className="flex gap-2">
          <input
            value={channelFilter}
            onChange={(e) => setChannelFilter(e.target.value)}
            placeholder="Channel filter..."
            className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg px-3 py-1.5 text-sm text-[#e8e8ec] outline-none focus:border-[#00e5ff]"
          />
          <button
            onClick={fetchJobs}
            className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg px-4 py-1.5 text-sm hover:border-[#00e5ff] transition-colors"
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Pipeline Jobs Table */}
      <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#2a2a36] text-[#7a7a8e] text-xs uppercase">
              <th className="text-left px-4 py-3">Job Code</th>
              <th className="text-left px-4 py-3">Channel</th>
              <th className="text-left px-4 py-3">Type</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Step</th>
              <th className="text-left px-4 py-3">Progress</th>
              <th className="text-left px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-[#7a7a8e]">
                  No pipelines found. Create one to get started.
                </td>
              </tr>
            )}
            {jobs.map((job) => (
              <tr key={job.job_id} className="border-b border-[#2a2a36] hover:bg-[#22222e]">
                <td className="px-4 py-3 font-mono text-xs">{job.job_code || job.job_id.slice(0, 8)}</td>
                <td className="px-4 py-3">{job.channel_id || '-'}</td>
                <td className="px-4 py-3">{job.content_type || 'flagship'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    job.status === 'running' ? 'bg-blue-900/50 text-blue-300' :
                    job.status === 'completed' ? 'bg-green-900/50 text-green-300' :
                    job.status === 'failed' ? 'bg-red-900/50 text-red-300' :
                    job.status === 'pending_approval' ? 'bg-yellow-900/50 text-yellow-300' :
                    'bg-[#2a2a36] text-[#7a7a8e]'
                  }`}>
                    {job.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-[#7a7a8e]">{job.current_step || '-'}</td>
                <td className="px-4 py-3">
                  <div className="w-20 h-1.5 bg-[#2a2a36] rounded-full overflow-hidden">
                    <div className="h-full bg-[#00e5ff] rounded-full" style={{ width: `${job.progress_pct || 0}%` }} />
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    {job.status === 'pending_approval' && (
                      <button onClick={() => handleApprove(job.job_id)} className="text-xs bg-green-900/30 text-green-400 px-2 py-1 rounded hover:bg-green-900/50">Approve</button>
                    )}
                    {job.status === 'completed' && (
                      <button onClick={() => handleRun(job.job_id)} className="text-xs bg-blue-900/30 text-blue-400 px-2 py-1 rounded hover:bg-blue-900/50">Rerun</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
