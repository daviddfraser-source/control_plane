"use client";

interface KpiCardProps {
  /** The display label shown as the card title */
  label?: string;
  /** Alternative to label — same thing, allows both naming conventions */
  title?: string;
  value: number | string;
  trend?: "up" | "down" | "neutral" | { delta: number; direction: "up" | "down" | "steady" };
  trendValue?: string;
  icon?: string;
  accent?: "primary" | "success" | "warning" | "danger";
}

const accentColors = {
  primary: "var(--primary)",
  success: "var(--success)",
  warning: "var(--warning)",
  danger: "var(--danger)",
};

export function KpiCard({ label, title, value, trend, trendValue, icon, accent = "primary" }: KpiCardProps) {
  const displayLabel = label ?? title ?? "";

  // Handle both the old { delta, direction } shape and the simple "up"/"down"/"neutral" string
  let trendColor = "var(--text-tertiary)";
  let trendArrow = "→";
  let trendDisplay = trendValue ?? "";

  if (trend) {
    if (typeof trend === "string") {
      // Simple string variant used by dashboard: "up" | "down" | "neutral"
      trendArrow = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";
      trendColor = trend === "up" ? "var(--success)" : trend === "down" ? "var(--danger)" : "var(--text-tertiary)";
    } else {
      // Legacy object variant: { delta, direction }
      trendArrow = trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→";
      trendColor = trend.direction === "up" ? "var(--danger)" : trend.direction === "down" ? "var(--success)" : "var(--text-tertiary)";
      if (!trendDisplay) trendDisplay = `${trend.delta >= 0 ? "+" : ""}${trend.delta}`;
    }
  }

  return (
    <div className="relative bg-token-surface border border-token-default rounded-[var(--radius-xl)] p-4 overflow-hidden transition-shadow hover:shadow-token-sm">
      <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-[3px]" style={{ background: accentColors[accent] }} />
      <div className="flex items-start justify-between mb-1">
        <h4 className="text-xs text-token-tertiary uppercase tracking-wide">{displayLabel}</h4>
        {icon && <span className="text-lg leading-none">{icon}</span>}
      </div>
      <div className="text-2xl font-bold text-token-primary">{value}</div>
      {trend && (
        <div className="text-xs mt-1 flex items-center gap-1" style={{ color: trendColor }}>
          <span>{trendArrow}</span>
          {trendDisplay && <span>{trendDisplay}</span>}
        </div>
      )}
    </div>
  );
}
