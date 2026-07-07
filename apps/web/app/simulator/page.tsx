'use client';

import { useState } from 'react';
import { generateMedia } from '@/lib/api';

type MediaType = 'image' | 'video' | 'music' | 'tts' | '3d' | 'meme';

const MEDIA_TABS: { key: MediaType; label: string }[] = [
  { key: 'image', label: 'Image' },
  { key: 'video', label: 'Video' },
  { key: 'music', label: 'Music' },
  { key: 'tts', label: 'TTS' },
  { key: '3d', label: '3D' },
  { key: 'meme', label: 'Meme' },
];

export default function SimulatorPage() {
  const [activeTab, setActiveTab] = useState<MediaType>('image');
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      let endpoint = '';
      let body: any = {};

      switch (activeTab) {
        case 'image':
          endpoint = '/api/image/generate';
          body = { prompt: prompt.trim() };
          break;
        case 'video':
          endpoint = '/api/video/generate';
          body = { prompt: prompt.trim() };
          break;
        case 'music':
          endpoint = '/api/music/generate';
          body = { prompt: prompt.trim() };
          break;
        case 'tts':
          endpoint = '/api/tts/synthesize';
          body = { text: prompt.trim() };
          break;
        case '3d':
          endpoint = '/api/3d/generate';
          body = { prompt: prompt.trim() };
          break;
        case 'meme':
          endpoint = '/api/meme/generate';
          body = { prompt: prompt.trim() };
          break;
      }

      const data = await generateMedia(endpoint, body);
      setResult(data);
    } catch (err: any) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-[#00e5ff]">Media Simulator</h1>
        <p className="text-[#7a7a8e] text-sm mt-1">Generate media with AI models</p>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {MEDIA_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setResult(null); }}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              activeTab === tab.key ? 'bg-[#00e5ff] text-black' : 'bg-[#1a1a22] border border-[#2a2a36] text-[#7a7a8e] hover:border-[#00e5ff]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl p-6 mb-6">
        <label className="text-xs text-[#7a7a8e] uppercase tracking-wider mb-2 block">
          {activeTab === 'tts' ? 'Text to speak' : 'Prompt'}
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={
            activeTab === 'image' ? 'A futuristic cityscape at sunset...' :
            activeTab === 'video' ? 'A timelapse of clouds moving over mountains...' :
            activeTab === 'music' ? 'Upbeat electronic dance music with synth pads...' :
            activeTab === 'tts' ? 'Enter text to convert to speech...' :
            activeTab === '3d' ? 'A detailed model of a sports car...' :
            'Describe the meme concept...'
          }
          rows={3}
          className="w-full bg-[#0f0f14] border border-[#2a2a36] rounded-lg px-4 py-3 text-sm text-[#e8e8ec] outline-none focus:border-[#00e5ff] resize-none"
        />
        <button
          onClick={handleGenerate}
          disabled={loading || !prompt.trim()}
          className="mt-4 bg-[#00e5ff] text-black px-6 py-2 rounded-lg text-sm font-medium hover:brightness-110 disabled:opacity-40"
        >
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl p-6">
          {result.error ? (
            <div className="text-red-400 text-sm">{result.error}</div>
          ) : (
            <div>
              <div className="text-sm text-[#7a7a8e] mb-2">Job submitted</div>
              <pre className="text-xs text-[#e8e8ec] bg-[#0f0f14] rounded-lg p-4 overflow-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
              {result.job_id && (
                <div className="mt-3 text-xs text-[#7a7a8e]">
                  Poll: <span className="text-[#00e5ff] font-mono">{result.poll_url}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
