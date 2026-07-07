'use client';

import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

interface GPUInfo {
  index: number;
  name: string;
  vram_used_mb: number;
  vram_total_mb: number;
  utilization_pct: number;
  temperature_c: number;
  power_w: number;
}

export default function DashboardPage() {
  const [health, setHealth] = useState<Record<string, string>>({});
  const [gpus, setGpus] = useState<Record<string, GPUInfo>>({});

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json()).then(d => setHealth(d.services || {}));
    fetch(`${API}/api/gpu/status`).then(r => r.json()).then(d => setGpus(d.gpus || {}));
  }, []);

  const navItems = [
    { label: 'IDE', href: '/ide', desc: 'Code editor with AI agent' },
    { label: 'Pipeline', href: '/pipeline', desc: 'Content pipeline dashboard' },
    { label: 'Mail', href: '/mail', desc: 'Email organization agent' },
    { label: 'Simulator', href: '/simulator', desc: 'Media generation playground' },
  ];

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-[#00e5ff]">Spark Media Factory V2</h1>
        <p className="text-[#7a7a8e] mt-2">AI-powered media generation and coding agent platform</p>
      </header>

      {/* Service Health */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#7a7a8e] mb-3">Services</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(health).map(([name, status]) => (
            <div key={name} className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg p-3">
              <div className="text-xs text-[#7a7a8e]">{name}</div>
              <div className={`text-sm font-medium mt-1 ${status === 'online' ? 'text-green-400' : 'text-red-400'}`}>
                {status}
              </div>
            </div>
          ))}
          {Object.keys(health).length === 0 && (
            <div className="text-xs text-[#7a7a8e] col-span-4">Loading...</div>
          )}
        </div>
      </section>

      {/* GPU Status */}
      {Object.keys(gpus).length > 0 && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[#7a7a8e] mb-3">GPU Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(gpus).map(([key, gpu]) => (
              <div key={key} className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg p-4">
                <div className="text-sm font-medium">{gpu.name}</div>
                <div className="mt-2 space-y-1 text-xs text-[#7a7a8e]">
                  <div>VRAM: {gpu.vram_used_mb}MB / {gpu.vram_total_mb}MB</div>
                  <div>Utilization: {gpu.utilization_pct}%</div>
                  <div>Temp: {gpu.temperature_c}°C | Power: {gpu.power_w}W</div>
                </div>
                <div className="mt-2 h-1.5 bg-[#2a2a36] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#00e5ff] rounded-full"
                    style={{ width: `${(gpu.vram_used_mb / gpu.vram_total_mb) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Navigation */}
      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[#7a7a8e] mb-3">Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="block bg-[#1a1a22] border border-[#2a2a36] rounded-xl p-6 hover:border-[#00e5ff] transition-colors"
            >
              <div className="text-lg font-semibold">{item.label}</div>
              <div className="text-xs text-[#7a7a8e] mt-2">{item.desc}</div>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
