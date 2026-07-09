'use client';

import { useEffect, useRef } from 'react';
import { gatewayUrl } from '@/lib/api';

interface MonacoEditorProps {
  file: string | null;
}

const LANG_MAP: Record<string, string> = {
  js: 'javascript', jsx: 'javascript', ts: 'typescript', tsx: 'typescript',
  py: 'python', rb: 'ruby', java: 'java', go: 'go', rs: 'rust',
  c: 'c', cpp: 'cpp', cs: 'csharp', h: 'c', hpp: 'cpp',
  html: 'html', htm: 'html', css: 'css', scss: 'scss', less: 'less',
  json: 'json', yaml: 'yaml', yml: 'yaml', xml: 'xml', toml: 'ini',
  sql: 'sql', sh: 'shell', bash: 'shell', zsh: 'shell',
  md: 'markdown', txt: 'plaintext', log: 'plaintext',
  vue: 'html', svelte: 'html', php: 'php', swift: 'swift',
  kt: 'kotlin', dart: 'dart', r: 'r', lua: 'lua',
  dockerfile: 'dockerfile', makefile: 'makefile',
};

function getLanguage(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase() ?? '';
  return LANG_MAP[ext] ?? 'plaintext';
}

const EMPTY_VALUE = '// No file open — select one from the explorer\n// or ask Spark to create one';

export function MonacoEditor({ file }: MonacoEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js';
    script.onload = () => {
      const require = (window as any).require;
      require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
      require(['vs/editor/editor.main'], (monaco: any) => {
        monacoRef.current = monaco;

        monaco.editor.defineTheme('spark-dark', {
          base: 'vs-dark',
          inherit: true,
          rules: [],
          colors: {
            'editor.background': '#0f0f14',
            'editor.foreground': '#e8e8ec',
            'editor.lineHighlightBackground': '#1a1a22',
            'editor.selectionBackground': '#264f78',
            'editorCursor.foreground': '#00e5ff',
            'editorLineNumber.foreground': '#555',
            'editorLineNumber.activeForeground': '#aaa',
          },
        });

        editorRef.current = monaco.editor.create(containerRef.current!, {
          value: EMPTY_VALUE,
          language: 'plaintext',
          theme: 'spark-dark',
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 13,
          minimap: { enabled: false },
          automaticLayout: true,
          readOnly: true,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          padding: { top: 12 },
          renderLineHighlight: 'all',
          cursorBlinking: 'smooth',
          smoothScrolling: true,
          domReadOnly: true,
          contextmenu: false,
        });
      });
    };
    document.head.appendChild(script);

    return () => {
      editorRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    if (!editorRef.current || !monacoRef.current) return;

    if (!file) {
      editorRef.current.setModel(
        monacoRef.current.editor.createModel(EMPTY_VALUE, 'plaintext')
      );
      editorRef.current.updateOptions({ readOnly: true });
      return;
    }

    editorRef.current.updateOptions({ readOnly: false });

    fetch(gatewayUrl(`/api/ide/file?path=${encodeURIComponent(file)}`))
      .then((r) => r.json())
      .then((data) => {
        if (data.status === 'ok') {
          const lang = getLanguage(file);
          const model = monacoRef.current.editor.createModel(data.content, lang);
          editorRef.current.setModel(model);
        }
      })
      .catch(() => {});
  }, [file]);

  return (
    <div className="h-full w-full" ref={containerRef} />
  );
}
