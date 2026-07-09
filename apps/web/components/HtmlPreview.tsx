'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

interface HtmlPreviewProps {
  htmlContent: string;
  onCapture?: (base64: string) => void;
}

export function HtmlPreview({ htmlContent, onCapture }: HtmlPreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  useEffect(() => {
    if (!iframeRef.current || !htmlContent) return;
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    iframeRef.current.src = url;
    return () => URL.revokeObjectURL(url);
  }, [htmlContent]);

  const captureScreenshot = useCallback(async () => {
    if (!iframeRef.current || !containerRef.current) return null;
    setIsCapturing(true);
    try {
      const iframe = iframeRef.current;
      let canvas: HTMLCanvasElement;
      try {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
        if (iframeDoc) {
          const html2canvas = (await import('html2canvas')).default;
          canvas = await html2canvas(iframeDoc.documentElement, {
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            scale: 1,
            width: iframeDoc.documentElement.scrollWidth,
            height: iframeDoc.documentElement.scrollHeight,
            windowWidth: iframeDoc.documentElement.scrollWidth,
            windowHeight: iframeDoc.documentElement.scrollHeight,
          });
        } else {
          throw new Error('Cannot access iframe');
        }
      } catch {
        const html2canvas = (await import('html2canvas')).default;
        canvas = await html2canvas(containerRef.current, {
          useCORS: true,
          allowTaint: true,
          scale: 1,
        });
      }
      const base64 = canvas.toDataURL('image/png').split(',')[1];
      onCapture?.(base64);
      return base64;
    } catch (err) {
      console.error('Screenshot capture failed:', err);
      return null;
    } finally {
      setIsCapturing(false);
    }
  }, [htmlContent, onCapture]);

  useEffect(() => {
    if (containerRef.current) {
      (containerRef.current as any).__captureScreenshot = captureScreenshot;
    }
  }, [captureScreenshot]);

  return (
    <div ref={containerRef} className="h-full w-full bg-white relative">
      {isCapturing && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10">
          <span className="text-white text-sm">Capturing full page...</span>
        </div>
      )}
      <iframe
        ref={iframeRef}
        title="HTML Preview"
        className="w-full h-full border-0"
        sandbox="allow-scripts allow-same-origin"
        style={{ overflow: 'auto' }}
      />
    </div>
  );
}

export function capturePreview(containerRef: HTMLDivElement | null): Promise<string | null> {
  if (!containerRef) return Promise.resolve(null);
  const fn = (containerRef as any).__captureScreenshot;
  return fn ? fn() : Promise.resolve(null);
}
