"use client";

const statusConfig: Record<string, { bg: string; text: string; icon: string }> = {
  pending: { bg: "var(--warning-50)", text: "#92400e", icon: "○" },
  in_progress: { bg: "var(--primary-50)", text: "var(--primary-800)", icon: "◉" },
  done: { bg: "var(--success-50)", text: "#065f46", icon: "✓" },
  failed: { bg: "var(--danger-50)", text: "var(--danger-700)", icon: "✕" },
  blocked: { bg: "var(--bg-inset)", text: "var(--text-tertiary)", icon: "⊘" },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${className}`}
      style={{ background: config.bg, color: config.text }}
    >
      <span>{config.icon}</span>
      {status.replace("_", " ")}
    </span>
  );
}
