'use client';

import { useState, useRef, useEffect } from 'react';
import { chat } from '@/lib/api';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const data = await chat(userMsg);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response || 'No response' }]);
    } catch (err: any) {
      setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto">
      <header className="p-4 border-b border-[#2a2a36]">
        <h1 className="text-lg font-bold text-[#00e5ff]">Chat</h1>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-[#7a7a8e] mt-12">
            <p className="text-lg">Start a conversation</p>
            <p className="text-sm mt-2">Ask anything about your projects, media, or code.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
              msg.role === 'user'
                ? 'bg-[#00e5ff] text-black'
                : 'bg-[#1a1a22] border border-[#2a2a36] text-[#e8e8ec]'
            }`}>
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-xl px-4 py-3 text-sm text-[#7a7a8e]">
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-[#2a2a36]">
        <div className="flex items-end gap-3">
          <div className="flex-1 bg-[#1a1a22] border border-[#2a2a36] rounded-xl px-4 py-3 focus-within:border-[#00e5ff] transition-colors">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Message Spark AI..."
              rows={1}
              className="w-full bg-transparent text-[#e8e8ec] resize-none outline-none text-sm"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="w-10 h-10 rounded-lg bg-[#00e5ff] text-black flex items-center justify-center disabled:opacity-40 hover:brightness-110 transition-all"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
