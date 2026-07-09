'use client';

import { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import { ApprovalCard } from './ApprovalCard';
import type { AgentEvent } from '@/lib/types';

interface ChatMessageProps {
  event: AgentEvent;
  onApprove?: (toolCallId: string) => void;
  onReject?: (toolCallId: string, feedback: string) => void;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 px-2 py-1 text-[10px] font-mono rounded bg-[#2a2a36] text-[#7a7a8e] hover:text-[#e8e8ec] hover:bg-[#3a3a4a] transition-colors"
    >
      {copied ? 'copied' : 'copy'}
    </button>
  );
}

function CodeBlock({ children, className, ...props }: React.HTMLAttributes<HTMLPreElement> & { children?: React.ReactNode }) {
  const match = /language-(\w+)/.exec(className || '');
  const lang = match?.[1] ?? '';
  const code = extractText(children);

  return (
    <div className="relative group">
      {lang && (
        <span className="absolute top-2 left-3 text-[10px] font-mono text-[#7a7a8e] uppercase">
          {lang}
        </span>
      )}
      <CopyButton text={code} />
      <pre className={className} {...props}>
        {children}
      </pre>
    </div>
  );
}

function extractText(node: React.ReactNode): string {
  if (typeof node === 'string') return node;
  if (typeof node === 'number') return String(node);
  if (!node) return '';
  if (Array.isArray(node)) return node.map(extractText).join('');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const el = node as any;
  if (el?.props) return extractText(el.props.children);
  return '';
}

export function ChatMessage({ event, onApprove, onReject }: ChatMessageProps) {
  const [collapsed, setCollapsed] = useState(true);

  if (event.type === 'user_message') {
    return (
      <div className="px-3 py-1.5">
        <div className="text-[10px] font-mono text-[#8b5cf6] mb-0.5">PK</div>
        <div className="text-[#e8e8ec] text-[13px] leading-normal whitespace-pre-wrap">
          {event.content ?? ''}
        </div>
      </div>
    );
  }

  if (event.type === 'text' || event.type === 'token') {
    const isToken = event.type === 'token';
    return (
      <div className="px-3 py-1.5">
        <div className="text-[10px] font-mono text-[#00e5ff] mb-0.5">Spark</div>
        <div className="prose prose-invert prose-sm max-w-none text-[#e8e8ec] text-[13px] leading-normal">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              pre: CodeBlock,
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return match ? (
                  <code className={className} {...props}>{children}</code>
                ) : (
                  <code className="bg-[#0a0a12] px-1 py-0.5 rounded text-[#00e5ff] font-mono text-[11px]" {...props}>{children}</code>
                );
              },
            }}
          >
            {event.content ?? ''}
          </ReactMarkdown>
          {isToken && <span className="inline-block w-1.5 h-3.5 bg-[#00e5ff] animate-pulse ml-0.5 align-middle" />}
        </div>
      </div>
    );
  }

  if (event.type === 'tool_call') {
    const toolName = event.tool_name ?? 'unknown';
    const argsStr = event.tool_args ? JSON.stringify(event.tool_args, null, 2) : null;

    return (
      <div className="mx-3 my-0.5 rounded border border-[#2a2a36] bg-[#1a1a22] overflow-hidden">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center gap-1.5 px-2 py-1 hover:bg-[#22222e] transition-colors text-left"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#3b82f6] pulse-dot shrink-0" />
          <span className="text-[#8b5cf6] font-mono text-[11px]">{toolName}</span>
          <span className="text-[#555] text-[9px] ml-auto">{collapsed ? '▸' : '▾'}</span>
        </button>
        {!collapsed && argsStr && (
          <div className="border-t border-[#2a2a36] px-2 py-1.5">
            <pre className="text-[10px] font-mono text-[#aaa] bg-[#0a0a12] rounded p-1.5 overflow-x-auto max-h-32 overflow-y-auto whitespace-pre-wrap">
              {argsStr}
            </pre>
          </div>
        )}
      </div>
    );
  }

  if (event.type === 'tool_result') {
    const resultStr = typeof event.tool_result === 'string'
      ? event.tool_result
      : JSON.stringify(event.tool_result, null, 2);
    const truncated = resultStr.length > 500;
    const isError = event.is_error;

    return (
      <div className="mx-3 my-0.5 rounded border border-[#2a2a36] bg-[#1a1a22] overflow-hidden">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center gap-1.5 px-2 py-1 hover:bg-[#22222e] transition-colors text-left"
        >
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${isError ? 'bg-[#ef4444]' : 'bg-[#22c55e]'}`} />
          <span className="text-[10px] font-mono text-[#7a7a8e]">result</span>
          <span className={`ml-auto text-[10px] font-mono ${isError ? 'text-[#ef4444]' : 'text-[#22c55e]'}`}>
            {isError ? 'failed' : 'done'}
          </span>
          <span className="text-[#555] text-[9px]">{collapsed ? '▸' : '▾'}</span>
        </button>
        {!collapsed && (
          <div className="border-t border-[#2a2a36] px-2 py-1.5">
            <pre className={`text-[10px] font-mono rounded p-1.5 overflow-x-auto whitespace-pre-wrap ${
              isError ? 'bg-[rgba(239,68,68,0.1)] text-[#ef4444]' : 'bg-[#0a0a12] text-[#aaa]'
            } ${truncated ? 'max-h-24 overflow-y-auto' : ''}`}>
              {truncated ? resultStr.slice(0, 500) : resultStr}
            </pre>
          </div>
        )}
      </div>
    );
  }

  if (event.type === 'error') {
    return (
      <div className="mx-3 my-0.5 bg-[rgba(239,68,68,0.1)] border border-[#ef4444] rounded px-2 py-1 text-[11px] text-[#ef4444]">
        {event.error}
      </div>
    );
  }

  if (event.type === 'state_change') {
    return null;
  }

  if (event.type === 'awaiting_file_write' || event.type === 'awaiting_command_run') {
    return (
      <ApprovalCard
        event={event}
        onApprove={onApprove!}
        onReject={onReject!}
      />
    );
  }

  return null;
}
