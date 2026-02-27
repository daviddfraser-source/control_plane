"use client";
import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Button } from "../ui/button";

interface TerminalDrawerProps {
  open: boolean;
  onClose: () => void;
  onExecute: (command: string) => Promise<string>;
  suggestions?: string[];
}

export function TerminalDrawer({ open, onClose, onExecute, suggestions = [] }: TerminalDrawerProps) {
  const [output, setOutput] = useState<string[]>(["$ terminal ready"]);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [histIdx, setHistIdx] = useState(-1);
  const outputRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (open) inputRef.current?.focus(); }, [open]);
  useEffect(() => { outputRef.current?.scrollTo(0, outputRef.current.scrollHeight); }, [output]);

  async function handleSubmit() {
    if (!input.trim()) return;
    const cmd = input.trim();
    setHistory(h => [...h.slice(-99), cmd]);
    setHistIdx(-1);
    setOutput(o => [...o, `$ ${cmd}`]);
    setInput("");
    try {
      const result = await onExecute(cmd);
      setOutput(o => [...o, result]);
    } catch (e: unknown) {
      setOutput(o => [...o, `[ERR] ${e instanceof Error ? e.message : "Unknown error"}`]);
    }
  }

  function handleKey(e: KeyboardEvent) {
    if (e.key === "Enter") { e.preventDefault(); handleSubmit(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); const idx = histIdx < 0 ? history.length - 1 : Math.max(0, histIdx - 1); setHistIdx(idx); setInput(history[idx] || ""); }
    else if (e.key === "ArrowDown") { e.preventDefault(); const idx = histIdx + 1; if (idx >= history.length) { setHistIdx(-1); setInput(""); } else { setHistIdx(idx); setInput(history[idx] || ""); } }
  }

  if (!open) return null;

  return (
    <div className="fixed bottom-0 left-[280px] right-[280px] h-[280px] bg-[#0b1020] text-[#d6def8] border-t-2 border-[#334155] z-[var(--z-overlay)] flex flex-col">
      <div className="flex justify-between items-center px-3 py-2 text-xs bg-[#111827] border-b border-[#1e293b] text-[#94a3b8]">
        <span>Sandboxed Developer Terminal</span>
        <div className="flex gap-1.5">
          <Button variant="ghost" size="sm" onClick={() => setOutput(["$ terminal cleared"])}>Clear</Button>
          <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
        </div>
      </div>
      <div ref={outputRef} className="flex-1 overflow-auto p-3 font-mono text-sm whitespace-pre-wrap leading-relaxed">
        {output.map((line, i) => (
          <div
            key={i}
            dangerouslySetInnerHTML={{
              __html: escapeHtml(line)
                .replace(/\[OK\]/g, '<span style="color:#4ade80">[OK]</span>')
                .replace(/\[ERR\]/g, '<span style="color:#f87171">[ERR]</span>')
                .replace(/\[WARN\]/g, '<span style="color:#fbbf24">[WARN]</span>')
                .replace(/^\$ /, '<span style="color:#22c55e">$ </span>'),
            }}
          />
        ))}
      </div>
      <div className="px-3 py-2 border-t border-[#1e293b]">
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          className="w-full bg-[#020617] text-[#e2e8f0] border border-[#334155] rounded-[var(--radius-md)] px-2 py-2 font-mono text-sm outline-none focus:border-[var(--primary-400)]"
          placeholder="substrate validate"
        />
      </div>
    </div>
  );
}
  function escapeHtml(text: string): string {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
