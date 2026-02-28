"use client";
import { useEffect, useState, useRef } from "react";

interface Command {
  label: string;
  icon?: string;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  commands: Command[];
}

function fuzzyMatch(text: string, query: string): boolean {
  let qi = 0;
  const lower = text.toLowerCase(), q = query.toLowerCase();
  for (let i = 0; i < lower.length && qi < q.length; i++) {
    if (lower[i] === q[qi]) qi++;
  }
  return qi === q.length;
}

export function CommandPalette({ open, onClose, commands }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = query ? (commands || []).filter(c => fuzzyMatch(c.label, query)) : (commands || []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setIndex(0);
      inputRef.current?.focus();
    }
  }, [open]);

  if (!open) return null;

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") { e.preventDefault(); setIndex(i => Math.min(filtered.length - 1, i + 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setIndex(i => Math.max(0, i - 1)); }
    else if (e.key === "Enter") { e.preventDefault(); filtered[index]?.action(); onClose(); }
    else if (e.key === "Escape") onClose();
  }

  return (
    <div className="fixed inset-0 z-[var(--z-modal)] flex items-start justify-center pt-[20vh] bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-token-surface border border-token-default rounded-[var(--radius-2xl)] w-[520px] max-w-[90vw] shadow-token-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
        <input
          ref={inputRef}
          className="w-full p-4 border-b border-token-muted text-lg bg-transparent text-token-primary outline-none"
          placeholder="Type a command..."
          value={query}
          onChange={e => { setQuery(e.target.value); setIndex(0); }}
          onKeyDown={handleKey}
        />
        <div className="max-h-[300px] overflow-y-auto">
          {filtered.length === 0 && <div className="p-4 text-center text-sm text-token-tertiary">No matching commands</div>}
          {filtered.map((cmd, i) => (
            <div
              key={cmd.label}
              className={`flex items-center gap-3 px-4 py-3 text-sm cursor-pointer transition-colors ${i === index ? "bg-[var(--primary-50)] text-[var(--primary-700)]" : "text-token-secondary"}`}
              onClick={() => { cmd.action(); onClose(); }}
              onMouseEnter={() => setIndex(i)}
            >
              {cmd.icon && <span className="w-5 text-center">{cmd.icon}</span>}
              <span className="flex-1">{cmd.label}</span>
              {cmd.shortcut && <span className="text-xs font-mono text-token-tertiary">{cmd.shortcut}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
