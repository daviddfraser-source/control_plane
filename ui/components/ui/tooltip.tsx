"use client";
import { useState, ReactNode } from "react";

interface TooltipProps {
  content: string;
  children: ReactNode;
}

export function Tooltip({ content, children }: TooltipProps) {
  const [show, setShow] = useState(false);
  return (
    <span className="relative inline-flex" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      {show && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded-[var(--radius-md)] bg-[var(--gray-900)] text-[var(--gray-50)] text-xs whitespace-nowrap z-[var(--z-tooltip)] shadow-token-md animate-[fadeIn_0.1s_ease-out]">
          {content}
        </span>
      )}
    </span>
  );
}
