"use client";

interface SkeletonProps {
  className?: string;
  height?: string;
}

export function Skeleton({ className = "", height = "48px" }: SkeletonProps) {
  return (
    <div
      className={`bg-token-inset rounded-[var(--radius-md)] relative overflow-hidden ${className}`}
      style={{ height }}
    >
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-[shimmer_1.5s_infinite]" />
    </div>
  );
}
