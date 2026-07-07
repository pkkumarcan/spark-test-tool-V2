'use client';

import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

interface Email {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
}

export default function MailPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [stats, setStats] = useState<any>({});

  const fetchEmails = async () => {
    try {
      const r = await fetch(`${API}/api/mail/emails`);
      if (r.ok) {
        const data = await r.json();
        setEmails(data.emails || data || []);
      }
    } catch {}
  };

  const fetchStats = async () => {
    try {
      const r = await fetch(`${API}/api/mail/stats`);
      if (r.ok) setStats(await r.json());
    } catch {}
  };

  useEffect(() => { fetchEmails(); fetchStats(); }, []);

  const startSync = async () => {
    setSyncing(true);
    try {
      await fetch(`${API}/api/mail/sync/start`, { method: 'POST' });
      setTimeout(() => { fetchEmails(); fetchStats(); setSyncing(false); }, 5000);
    } catch { setSyncing(false); }
  };

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#00e5ff]">Mail Agent</h1>
          <p className="text-[#7a7a8e] text-sm mt-1">AI-powered email organization</p>
        </div>
        <button
          onClick={startSync}
          disabled={syncing}
          className="bg-[#00e5ff] text-black px-4 py-2 rounded-lg text-sm font-medium hover:brightness-110 disabled:opacity-40"
        >
          {syncing ? 'Syncing...' : 'Sync Email'}
        </button>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        {Object.entries(stats).filter(([k]) => !['senders', 'recent'].includes(k)).map(([k, v]) => (
          <div key={k} className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg p-3">
            <div className="text-xs text-[#7a7a8e]">{k}</div>
            <div className="text-lg font-semibold mt-1">{String(v)}</div>
          </div>
        ))}
      </div>

      {/* Email List */}
      <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[#2a2a36]">
          <h2 className="text-sm font-semibold">Inbox</h2>
        </div>
        {emails.length === 0 && (
          <div className="px-4 py-8 text-center text-[#7a7a8e] text-sm">
            No emails. Click Sync to fetch.
          </div>
        )}
        {emails.map((email) => (
          <div key={email.id} className="px-4 py-3 border-b border-[#2a2a36] hover:bg-[#22222e]">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">{email.subject}</div>
              <div className="text-xs text-[#7a7a8e]">{email.date}</div>
            </div>
            <div className="text-xs text-[#7a7a8e] mt-1">From: {email.from}</div>
            {email.snippet && (
              <div className="text-xs text-[#5a5a6e] mt-1 truncate">{email.snippet}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
