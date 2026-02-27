"use client";

import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className = "", hover = true, ...rest }: CardProps) {
  return (
    <div
      className={`bg-token-surface border border-token-default rounded-[var(--radius-xl)] p-4 transition-shadow ${hover ? "hover:shadow-token-sm" : ""} ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
