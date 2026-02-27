"use client";

import { KpiCard } from "@/components/governance/KpiCard";
import { ProgressRing } from "@/components/governance/ProgressRing";
import { DependencyGraph } from "@/components/governance/DependencyGraph";
import { getDashboardSnapshot } from "@/lib/product/ops-data";

export default function DashboardPage() {
  const snapshot = getDashboardSnapshot();
  const counts = snapshot.counts;
  const total = snapshot.total;
  const completionRate = total > 0 ? Math.round((counts.done / total) * 100) : 0;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-token-primary mb-1">Operational Dashboard</h1>
        <p className="text-sm text-token-secondary">Real-time governance snapshot</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Total Packets" value={total} trend="neutral" icon="📦" />
        <KpiCard label="Completed" value={counts.done} trend="up" trendValue={`${completionRate}%`} icon="✅" />
        <KpiCard label="In Progress" value={counts.in_progress} trend="neutral" icon="⏳" />
        <KpiCard
          label="Blocked"
          value={counts.blocked}
          trend={counts.blocked > 0 ? "down" : "neutral"}
          icon="🚫"
        />
      </div>

      <div className="bg-token-elevated rounded-lg border border-token-border-default p-6">
        <h2 className="text-lg font-semibold text-token-primary mb-4">Completion Progress</h2>
        <div className="flex items-center gap-8">
          <ProgressRing percentage={completionRate} size={120} strokeWidth={10} />
          <div className="space-y-2">
            <p className="text-sm text-token-secondary">Completion Rate</p>
            <p className="text-3xl font-bold text-token-primary">{completionRate}%</p>
            <p className="text-xs text-token-tertiary">
              {counts.done} of {total} packets completed
            </p>
          </div>
        </div>
      </div>

      <div className="bg-token-elevated rounded-lg border border-token-border-default p-6">
        <h2 className="text-lg font-semibold text-token-primary mb-4">Dependency Graph</h2>
        {snapshot.nodes.length ? (
          <DependencyGraph nodes={snapshot.nodes} edges={snapshot.edges} />
        ) : (
          <p className="text-sm text-token-secondary">No dependency data available</p>
        )}
      </div>
    </div>
  );
}
