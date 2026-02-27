"use client";

import { useMemo } from "react";

interface TtydDockProps {
  open: boolean;
  onClose: () => void;
}

export function TtydDock({ open, onClose }: TtydDockProps) {
  const ttydUrl = useMemo(() => {
    const configured = process.env.NEXT_PUBLIC_TTYD_URL;
    if (configured) return configured;
    if (typeof window !== "undefined") {
      return `${window.location.protocol}//${window.location.hostname}:7681`;
    }
    return "http://127.0.0.1:7681";
  }, []);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/35">
      <div className="absolute inset-x-4 bottom-4 top-20 rounded-xl border border-token-border-default bg-token-elevated shadow-2xl overflow-hidden">
        <div className="h-12 px-4 border-b border-token-border-default bg-token-inset flex items-center justify-between">
          <div className="text-sm font-medium text-token-primary">Embedded CLI (ttyd)</div>
          <div className="flex items-center gap-3">
            <a
              href={ttydUrl}
              target="_blank"
              rel="noreferrer"
              className="text-xs underline text-token-secondary hover:text-token-primary"
            >
              Open in tab
            </a>
            <button
              onClick={onClose}
              className="px-2 py-1 text-xs border border-token-border-default rounded bg-token-elevated text-token-secondary hover:text-token-primary"
            >
              Close
            </button>
          </div>
        </div>
        <iframe
          key={ttydUrl}
          src={ttydUrl}
          title="ttyd terminal dock"
          className="w-full h-[calc(100%-3rem)] bg-black"
        />
      </div>
    </div>
  );
}
