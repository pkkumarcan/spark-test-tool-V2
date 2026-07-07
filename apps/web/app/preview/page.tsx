'use client';

import { useState, useEffect } from 'react';
import { fetchAssets, type Asset } from '@/lib/api';

export default function PreviewPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState<Asset | null>(null);

  useEffect(() => {
    fetchAssets().then(setAssets).catch(() => {});
  }, []);

  const filtered = filter === 'all' ? assets : assets.filter(a => a.type === filter);
  const types = ['all', 'image', 'video', 'audio', 'doc'];

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-[#00e5ff]">Asset Preview</h1>
        <p className="text-[#7a7a8e] text-sm mt-1">Browse and preview generated assets</p>
      </header>

      {/* Filter */}
      <div className="flex gap-2 mb-6">
        {types.map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`px-3 py-1 rounded-lg text-xs transition-colors ${
              filter === t ? 'bg-[#00e5ff] text-black' : 'bg-[#1a1a22] border border-[#2a2a36] text-[#7a7a8e] hover:border-[#00e5ff]'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Asset Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {filtered.map((asset, i) => (
          <div
            key={i}
            onClick={() => setSelected(asset)}
            className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl p-3 cursor-pointer hover:border-[#00e5ff] transition-colors"
          >
            {asset.type === 'image' && (
              <div className="aspect-square bg-[#2a2a36] rounded-lg mb-2 flex items-center justify-center text-[#7a7a8e]">
                IMG
              </div>
            )}
            {asset.type === 'video' && (
              <div className="aspect-video bg-[#2a2a36] rounded-lg mb-2 flex items-center justify-center text-[#7a7a8e]">
                VID
              </div>
            )}
            {asset.type === 'audio' && (
              <div className="aspect-square bg-[#2a2a36] rounded-lg mb-2 flex items-center justify-center text-[#7a7a8e]">
                AUD
              </div>
            )}
            {asset.type === 'doc' && (
              <div className="aspect-square bg-[#2a2a36] rounded-lg mb-2 flex items-center justify-center text-[#7a7a8e]">
                DOC
              </div>
            )}
            <div className="text-xs truncate">{asset.name}</div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center text-[#7a7a8e] py-12">No assets found.</div>
      )}

      {/* Preview Modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-8" onClick={() => setSelected(null)}>
          <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl max-w-3xl w-full p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">{selected.name}</h3>
              <button onClick={() => setSelected(null)} className="text-[#7a7a8e] hover:text-white">✕</button>
            </div>
            {selected.type === 'image' && (
              <img src={selected.url} alt={selected.name} className="w-full rounded-lg" />
            )}
            {selected.type === 'video' && (
              <video src={selected.url} controls className="w-full rounded-lg" />
            )}
            {selected.type === 'audio' && (
              <audio src={selected.url} controls className="w-full" />
            )}
            {selected.type === 'doc' && (
              <div className="bg-[#0f0f14] rounded-lg p-4 text-sm">
                <a href={selected.url} className="text-[#00e5ff] underline">{selected.name}</a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
