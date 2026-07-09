'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { listPipelines, createPipeline, runPipeline, approvePipeline, type PipelineJob } from '@/lib/api';

const CHANNELS = [
  { code: 'DFW', name: 'Drift Wave', niche: 'Lofi Music' },
  { code: 'STM', name: 'Still Mind', niche: 'Stoicism' },
  { code: 'ODA', name: 'Odd Archive', niche: 'Mystery/History' },
  { code: 'PKP', name: 'Peak Protocol', niche: 'Biohacking' },
  { code: 'DKS', name: 'Dark Signal', niche: 'Dark Psychology' },
  { code: 'GDB', name: 'Ground Brief', niche: 'Geopolitics+Macro' },
  { code: 'ISL', name: 'Inner Scroll', niche: 'Vedic/Spiritual' },
  { code: 'NHZ', name: 'Next Horizon', niche: 'Future Tech' },
  { code: 'RMR', name: 'Roam Rich', niche: 'Digital Nomad' },
  { code: 'BWA', name: 'Build With AI', niche: 'AI Tutorials' },
];

const STAGES = [
  { key: 'topic', label: 'Topic Brief', icon: '01' },
  { key: 'script', label: 'Script', icon: '02' },
  { key: 'approval', label: 'Approval', icon: '03' },
  { key: 'voiceover', label: 'Voiceover', icon: '04' },
  { key: 'visuals', label: 'Visuals', icon: '05' },
  { key: 'upscale', label: 'Upscale', icon: '06' },
  { key: 'stitch', label: 'Stitch', icon: '07' },
  { key: 'qc', label: 'QC', icon: '08' },
  { key: 'publish', label: 'Publish', icon: '09' },
];

function getGatewayHost() {
  if (typeof window !== 'undefined') return `${window.location.protocol}//${window.location.hostname}:8080`;
  return 'http://localhost:8080';
}

export default function PipelinePage() {
  const [jobs, setJobs] = useState<PipelineJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<PipelineJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [newChannelId, setNewChannelId] = useState('STM');
  const [newTopic, setNewTopic] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await listPipelines();
      setJobs(data);
      if (selectedJob) {
        const updated = data.find((j: PipelineJob) => j.job_id === selectedJob.job_id);
        if (updated) setSelectedJob(updated);
      }
    } catch {}
  }, [selectedJob]);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  const handleApprove = async (pipelineId: string) => {
    setLoading(true);
    try { await approvePipeline(pipelineId); fetchJobs(); } finally { setLoading(false); }
  };

  const handleRun = async (pipelineId: string) => {
    setLoading(true);
    try { await runPipeline(pipelineId); fetchJobs(); } finally { setLoading(false); }
  };

  const handleLaunch = async () => {
    if (!newTopic.trim()) return;
    setSubmitting(true);
    try {
      const job = await createPipeline(newChannelId, newTopic.trim());
      await runPipeline(job.job_id);
      setNewTopic('');
      fetchJobs();
    } finally { setSubmitting(false); }
  };

  const videoUrl = selectedJob?.status === 'completed'
    ? `${getGatewayHost()}/api/pipeline/${selectedJob.job_id}/output/final/video_final.mp4`
    : null;

  return (
    <div className="flex h-screen bg-[#0d0f14] text-[#e8e8ec] overflow-hidden">
      {/* Left Sidebar — Job History */}
      <aside className="w-72 bg-[#13161e] border-r border-[#222236] flex flex-col overflow-hidden flex-shrink-0">
        {/* Sidebar Header */}
        <div className="p-3 border-b border-[#222236]">
          <h2 className="text-xs font-semibold text-[#7a7a8e] uppercase tracking-wider mb-3">Pipeline Jobs</h2>
          {/* Launch Form */}
          <select
            value={newChannelId}
            onChange={(e) => setNewChannelId(e.target.value)}
            className="w-full bg-[#1a1d28] border border-[#2a2a36] rounded-md px-2 py-1.5 text-xs text-[#e8e8ec] outline-none focus:border-[#00e5ff] mb-2"
          >
            {CHANNELS.map((ch) => (
              <option key={ch.code} value={ch.code}>{ch.code} — {ch.name}</option>
            ))}
          </select>
          <input
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            placeholder="Enter topic..."
            className="w-full bg-[#1a1d28] border border-[#2a2a36] rounded-md px-2 py-1.5 text-xs text-[#e8e8ec] outline-none focus:border-[#00e5ff] mb-2"
            onKeyDown={(e) => { if (e.key === 'Enter') handleLaunch(); }}
          />
          <button
            onClick={handleLaunch}
            disabled={submitting || !newTopic.trim()}
            className="w-full bg-[#10b981] text-black font-semibold text-xs rounded-md py-1.5 hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {submitting ? 'Launching...' : 'Launch Pipeline'}
          </button>
        </div>

        {/* Job List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
          {jobs.length === 0 && (
            <div className="text-center text-[#52576b] text-xs py-8">No pipelines yet</div>
          )}
          {jobs.map((job) => (
            <div
              key={job.job_id}
              onClick={() => setSelectedJob(job)}
              className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-all border ${
                selectedJob?.job_id === job.job_id
                  ? 'bg-[#21263a] border-[#3a3a46]'
                  : 'bg-[#1a1d28] border-transparent hover:bg-[#21263a] hover:border-[#2a2a36]'
              }`}
            >
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                job.status === 'completed' ? 'bg-[#10b981]' :
                job.status === 'running' ? 'bg-[#3b82f6] shadow-[0_0_4px_#3b82f6]' :
                job.status === 'failed' ? 'bg-[#ef4444]' :
                job.status === 'pending_approval' ? 'bg-[#f59e0b] shadow-[0_0_4px_#f59e0b]' :
                'bg-[#52576b]'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="text-[11px] font-semibold text-[#f0f2f5] truncate">{job.topic || 'Untitled'}</div>
                <div className="text-[9px] text-[#52576b] font-mono">{job.channel_id || '—'} · {job.job_code || job.job_id.slice(0, 8)}</div>
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-5 py-2.5 bg-[#13161e] border-b border-[#222236] flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded bg-[#10b981] flex items-center justify-center text-black text-sm font-bold">S</div>
            <span className="text-sm font-semibold text-[#f0f2f5]" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Spark Media Factory</span>
            <span className="text-[10px] text-[#52576b] bg-[#21263a] px-2 py-0.5 rounded">v3.0</span>
          </div>
          <div className="flex items-center gap-3">
            {selectedJob?.status === 'running' && (
              <div className="flex items-center gap-1.5 text-[10px] text-[#10b981] bg-[rgba(16,185,129,0.12)] border border-[rgba(16,185,129,0.25)] px-2.5 py-1 rounded-full font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
                {selectedJob.channel_id} · {selectedJob.current_step || 'running'}
              </div>
            )}
            <button onClick={fetchJobs} className="text-xs text-[#7a7a8e] bg-[#1a1d28] border border-[#2a2a36] rounded-md px-3 py-1 hover:border-[#00e5ff] transition-colors">
              Refresh
            </button>
          </div>
        </header>

        {/* Pipeline Stepper */}
        {selectedJob && (
          <div className="flex items-center gap-1 px-4 py-2 bg-[#13161e] border-b border-[#222236] overflow-x-auto flex-shrink-0">
            {STAGES.map((stage, i) => {
              const stageData = selectedJob.stage ? (selectedJob as any).stages?.[stage.key] : null;
              const status = stageData?.status || 'pending';
              const isActive = selectedJob.stage === stage.key;
              const isCompleted = status === 'passed' || status === 'completed';
              const isFailed = status === 'failed';
              return (
                <div key={stage.key} className="flex items-center gap-1 flex-shrink-0">
                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded text-[11px] transition-all ${
                    isActive ? 'text-[#3b82f6] font-semibold bg-[rgba(59,130,246,0.08)] border border-[rgba(59,130,246,0.2)]' :
                    isCompleted ? 'text-[#10b981]' :
                    isFailed ? 'text-[#ef4444]' :
                    'text-[#52576b]'
                  }`}>
                    <span className="text-[9px] font-mono opacity-60">{stage.icon}</span>
                    {stage.label}
                    {isCompleted && <span className="text-[#10b981]">✓</span>}
                    {isFailed && <span className="text-[#ef4444]">✗</span>}
                  </div>
                  {i < STAGES.length - 1 && <div className="w-3 h-px bg-[#222236]" />}
                </div>
              );
            })}
          </div>
        )}

        {/* Main View Area */}
        <div className="flex-1 overflow-hidden p-5">
          {!selectedJob ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-[#52576b]">
                <div className="text-4xl mb-3">⚡</div>
                <div className="text-sm font-semibold" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Select a pipeline</div>
                <div className="text-xs mt-1">Choose a job from the sidebar or launch a new one</div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-[1fr_320px] gap-5 h-full">
              {/* Left: Video Player + Stage Details */}
              <div className="flex flex-col gap-4 overflow-y-auto">
                {/* Video Player */}
                <div className="bg-[#0a0a12] rounded-lg border border-[#222236] overflow-hidden">
                  <div className="aspect-video flex items-center justify-center relative">
                    {videoUrl ? (
                      <video
                        ref={videoRef}
                        key={videoUrl}
                        controls
                        className="w-full h-full object-contain"
                        src={videoUrl}
                      />
                    ) : (
                      <div className="text-center text-[#52576b] p-8">
                        <div className="text-3xl mb-2">🎬</div>
                        <div className="text-xs font-semibold">No video available</div>
                        <div className="text-[10px] mt-1">
                          {selectedJob.status === 'running' ? 'Video will appear here when pipeline completes' :
                           selectedJob.status === 'completed' ? 'Video processing...' :
                           'Complete the pipeline to generate video'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Stage Detail Cards */}
                <div className="grid grid-cols-3 gap-3">
                  {STAGES.map((stage) => {
                    const stageData = (selectedJob as any).stages?.[stage.key];
                    const status = stageData?.status || 'pending';
                    const msg = stageData?.msg || '';
                    return (
                      <div key={stage.key} className={`p-3 rounded-lg border ${
                        selectedJob.stage === stage.key ? 'bg-[#1a1d28] border-[#3a3a46]' :
                        status === 'passed' ? 'bg-[rgba(16,185,129,0.03)] border-[rgba(16,185,129,0.15)]' :
                        'bg-[#13161e] border-[#222236]'
                      }`}>
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className="text-[9px] font-mono bg-[rgba(255,255,255,0.03)] px-1.5 py-0.5 rounded text-[#7a7a8e]">{stage.icon}</span>
                          <span className="text-[11px] font-medium text-[#e8e8ec]">{stage.label}</span>
                        </div>
                        <div className={`text-[10px] ${
                          status === 'passed' ? 'text-[#10b981]' :
                          status === 'running' ? 'text-[#3b82f6]' :
                          status === 'failed' ? 'text-[#ef4444]' :
                          'text-[#52576b]'
                        }`}>
                          {msg || status}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right: Job Info Panel */}
              <div className="bg-[#13161e] rounded-lg border border-[#222236] p-4 overflow-y-auto flex flex-col gap-4">
                <div>
                  <h3 className="text-xs font-semibold text-[#7a7a8e] uppercase tracking-wider mb-2">Job Info</h3>
                  <div className="space-y-1.5 text-[11px]">
                    <div className="flex justify-between"><span className="text-[#52576b]">ID</span><span className="font-mono text-[#e8e8ec]">{selectedJob.job_code || selectedJob.job_id.slice(0, 12)}</span></div>
                    <div className="flex justify-between"><span className="text-[#52576b]">Channel</span><span className="text-[#e8e8ec]">{selectedJob.channel_id}</span></div>
                    <div className="flex justify-between"><span className="text-[#52576b]">Status</span>
                      <span className={`font-semibold ${
                        selectedJob.status === 'completed' ? 'text-[#10b981]' :
                        selectedJob.status === 'running' ? 'text-[#3b82f6]' :
                        selectedJob.status === 'failed' ? 'text-[#ef4444]' :
                        'text-[#7a7a8e]'
                      }`}>{selectedJob.status}</span>
                    </div>
                    <div className="flex justify-between"><span className="text-[#52576b]">Progress</span><span className="text-[#e8e8ec]">{selectedJob.progress_pct || 0}%</span></div>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-semibold text-[#7a7a8e] uppercase tracking-wider mb-2">Topic</h3>
                  <div className="text-[11px] text-[#e8e8ec] leading-relaxed">{selectedJob.topic || '—'}</div>
                </div>

                {/* Progress Bar */}
                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-[#52576b]">Pipeline Progress</span>
                    <span className="font-mono text-[#e8e8ec]">{selectedJob.progress_pct || 0}%</span>
                  </div>
                  <div className="h-2 bg-[#21263a] rounded-full overflow-hidden">
                    <div className="h-full bg-[#10b981] rounded-full transition-all" style={{ width: `${selectedJob.progress_pct || 0}%` }} />
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-auto space-y-2">
                  {selectedJob.status === 'pending_approval' && (
                    <button onClick={() => handleApprove(selectedJob.job_id)} className="w-full bg-[#10b981] text-black font-semibold text-xs rounded-md py-2 hover:brightness-110 transition-all">
                      Approve & Continue
                    </button>
                  )}
                  {selectedJob.status === 'completed' && (
                    <button onClick={() => handleRun(selectedJob.job_id)} className="w-full bg-[#1a1d28] border border-[#2a2a36] text-[#7a7a8e] font-semibold text-xs rounded-md py-2 hover:border-[#3b82f6] hover:text-[#3b82f6] transition-all">
                      Rerun Pipeline
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
