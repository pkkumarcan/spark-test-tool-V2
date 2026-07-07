'use client';

import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PipelineV2 {
  pipeline_id: string;
  channel_id: string;
  topic: string;
  stage: string;
  status: string;
  progress_pct: number;
  created_at: string;
}

export default function PipelineV2Page() {
  const [pipelines, setPipelines] = useState<PipelineV2[]>([]);
  const [channelId, setChannelId] = useState('MLN');
  const [topic, setTopic] = useState('');

  const fetchPipelines = async () => {
    const r = await fetch(`${API}/api/pipeline/list`);
    if (r.ok) {
      const data = await r.json();
      setPipelines(Array.isArray(data) ? data : data.pipelines || []);
    }
  };

  useEffect(() => { fetchPipelines(); }, []);

  const handleCreate = async () => {
    if (!topic.trim()) return;
    await fetch(`${API}/api/pipeline/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel_id: channelId, topic: topic.trim() }),
    });
    setTopic('');
    fetchPipelines();
  };

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-[#00e5ff]">Pipeline V2</h1>
        <p className="text-[#7a7a8e] text-sm mt-1">Stateful pipeline with approval gates</p>
      </header>

      <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl p-6 mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#7a7a8e] mb-4">Create Pipeline</h2>
        <div className="flex gap-3">
          <input
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            placeholder="Channel ID"
            className="w-24 bg-[#0f0f14] border border-[#2a2a36] rounded-lg px-3 py-2 text-sm outline-none focus:border-[#00e5ff]"
          />
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Topic..."
            className="flex-1 bg-[#0f0f14] border border-[#2a2a36] rounded-lg px-3 py-2 text-sm outline-none focus:border-[#00e5ff]"
          />
          <button
            onClick={handleCreate}
            className="bg-[#00e5ff] text-black px-6 py-2 rounded-lg text-sm font-medium hover:brightness-110"
          >
            Create
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {pipelines.map((p) => (
          <div key={p.pipeline_id} className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl p-4 flex items-center justify-between">
            <div>
              <div className="font-mono text-xs text-[#7a7a8e]">{p.pipeline_id.slice(0, 8)}</div>
              <div className="text-sm mt-1">{p.topic || 'No topic'}</div>
              <div className="text-xs text-[#7a7a8e] mt-1">Channel: {p.channel_id} | Stage: {p.stage}</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-24 h-1.5 bg-[#2a2a36] rounded-full overflow-hidden">
                <div className="h-full bg-[#00e5ff] rounded-full" style={{ width: `${p.progress_pct || 0}%` }} />
              </div>
              <span className={`px-2 py-0.5 rounded text-xs ${
                p.status === 'running' ? 'bg-blue-900/50 text-blue-300' :
                p.status === 'completed' ? 'bg-green-900/50 text-green-300' :
                'bg-[#2a2a36] text-[#7a7a8e]'
              }`}>
                {p.status}
              </span>
            </div>
          </div>
        ))}
        {pipelines.length === 0 && (
          <div className="text-center text-[#7a7a8e] py-12">No pipelines yet. Create one above.</div>
        )}
      </div>
    </div>
  );
}
