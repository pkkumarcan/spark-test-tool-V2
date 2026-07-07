'use client';

import type { AgentEvent } from '@/lib/types';

interface GenerativeUIProps {
  event: AgentEvent;
}

export function GenerativeUI({ event }: GenerativeUIProps) {
  if (event.type === 'tool_result' && typeof event.tool_result === 'string') {
    const result = event.tool_result;

    if (result.startsWith('## ') || result.includes('**Price') || result.includes('**Volume')) {
      return <MarkdownResult content={result} />;
    }

    if (result.includes('[DIR]') || result.includes('[FILE]')) {
      return <FileListResult content={result} />;
    }

    if (result.includes('Exit Code:')) {
      return <CommandResult content={result} />;
    }

    if (result.includes('Security scan') || result.includes('[HIGH]') || result.includes('[MEDIUM]')) {
      return <SecurityResult content={result} />;
    }

    return <TextResult content={result} />;
  }

  return null;
}

function MarkdownResult({ content }: { content: string }) {
  return (
    <div className="bg-[#1a1a22] border border-[#2a2a36] rounded-lg p-3 text-xs text-[#e8e8ec] whitespace-pre-wrap">
      {content.split('\n').map((line, i) => {
        if (line.startsWith('## ')) {
          return <h3 key={i} className="text-sm font-bold text-[#00e5ff] mt-2 mb-1">{line.slice(3)}</h3>;
        }
        if (line.startsWith('### ')) {
          return <h4 key={i} className="text-xs font-semibold text-[#8b5cf6] mt-2">{line.slice(4)}</h4>;
        }
        if (line.startsWith('**') && line.endsWith('**')) {
          return <div key={i} className="font-semibold mt-2">{line.replace(/\*\*/g, '')}</div>;
        }
        if (line.startsWith('- ')) {
          return <div key={i} className="pl-2 text-[#aaa]">• {line.slice(2)}</div>;
        }
        return <div key={i}>{line}</div>;
      })}
    </div>
  );
}

function FileListResult({ content }: { content: string }) {
  return (
    <div className="bg-[#0a0a12] border border-[#2a2a36] rounded-lg p-2 font-mono text-[10px]">
      {content.split('\n').map((line, i) => {
        if (line.startsWith('[DIR]')) {
          return <div key={i} className="text-[#8b5cf6]">{line}</div>;
        }
        if (line.startsWith('[FILE]')) {
          return <div key={i} className="text-[#aaa]">{line}</div>;
        }
        return <div key={i}>{line}</div>;
      })}
    </div>
  );
}

function CommandResult({ content }: { content: string }) {
  const lines = content.split('\n');
  const exitCode = lines[0];
  const isOk = exitCode.includes('Exit Code: 0');

  return (
    <div className="bg-[#0a0a12] border border-[#2a2a36] rounded-lg overflow-hidden">
      <div className={`px-3 py-1.5 text-[10px] font-semibold ${isOk ? 'bg-[rgba(34,197,94,0.1)] text-[#22c55e]' : 'bg-[rgba(239,68,68,0.1)] text-[#ef4444]'}`}>
        {exitCode}
      </div>
      <pre className="p-3 font-mono text-[10px] text-[#aaa] whitespace-pre-wrap overflow-x-auto max-h-[200px] overflow-y-auto">
        {lines.slice(1).join('\n')}
      </pre>
    </div>
  );
}

function SecurityResult({ content }: { content: string }) {
  return (
    <div className="bg-[rgba(239,68,68,0.05)] border border-[rgba(239,68,68,0.3)] rounded-lg p-3 text-xs">
      <div className="text-[#ef4444] font-semibold mb-2">Security Scan Results</div>
      <pre className="font-mono text-[10px] text-[#aaa] whitespace-pre-wrap">{content}</pre>
    </div>
  );
}

function TextResult({ content }: { content: string }) {
  return (
    <div className="bg-[#0a0a12] rounded-lg p-2 font-mono text-[10px] text-[#aaa] whitespace-pre-wrap overflow-hidden max-h-32">
      {content.slice(0, 500)}
      {content.length > 500 && <span className="text-[#555]">... ({content.length} chars)</span>}
    </div>
  );
}
