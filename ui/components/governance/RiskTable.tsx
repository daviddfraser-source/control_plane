"use client";

interface RiskEntry {
  id: string;
  title: string;
  severity: "high" | "medium" | "low" | "critical";
  status: string;
  owner?: string;
}

interface RiskTableProps {
  risks: RiskEntry[];
}

const severityColors = {
  high: { bg: "var(--danger-50)", text: "var(--danger-700)" },
  medium: { bg: "var(--warning-50)", text: "#92400e" },
  low: { bg: "var(--success-50)", text: "var(--success-700)" },
  critical: { bg: "var(--danger-100)", text: "var(--danger-800)" },
};

export function RiskTable({ risks }: RiskTableProps) {
  return (
    <div className="border border-token-default rounded-[var(--radius-xl)] overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-token-secondary text-token-secondary">
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">Risk</th>
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">Severity</th>
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">Status</th>
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">Owner</th>
          </tr>
        </thead>
        <tbody>
          {risks.map(risk => (
            <tr key={risk.id} className="border-t border-token-muted hover:bg-token-inset">
              <td className="px-4 py-2.5 font-medium">{risk.title}</td>
              <td className="px-4 py-2.5">
                <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold uppercase" style={{ background: severityColors[risk.severity].bg, color: severityColors[risk.severity].text }}>
                  {risk.severity}
                </span>
              </td>
              <td className="px-4 py-2.5 text-token-secondary">{risk.status}</td>
              <td className="px-4 py-2.5 text-token-tertiary">{risk.owner || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {risks.length === 0 && <div className="text-center py-8 text-sm text-token-tertiary">No risks registered</div>}
    </div>
  );
}
