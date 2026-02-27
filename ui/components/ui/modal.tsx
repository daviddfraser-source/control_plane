"use client";
import { useEffect, useRef, ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const firstFocusRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) firstFocusRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center bg-black/40 backdrop-blur-[4px] animate-[fadeIn_0.15s_ease-out]"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className="bg-token-surface rounded-[var(--radius-2xl)] w-[90%] max-w-[560px] max-h-[90vh] overflow-hidden shadow-token-2xl border border-token-default animate-[modalIn_0.2s_ease-out]">
        {title && (
          <div className="flex items-center justify-between px-6 py-5 border-b border-token-default">
            <h2 className="text-lg font-semibold">{title}</h2>
            <button ref={firstFocusRef} onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-[var(--radius-md)] text-token-tertiary hover:text-token-primary hover:bg-token-inset transition-all">&times;</button>
          </div>
        )}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">{children}</div>
        {footer && <div className="flex justify-end gap-3 px-6 py-4 border-t border-token-default">{footer}</div>}
      </div>
    </div>
  );
}
