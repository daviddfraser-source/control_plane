"use client";

import { useEffect, useState } from "react";

interface IntegrityStatus {
  ok: boolean;
  packet_count: number;
  commit_count: number;
  checkpoint_count: number;
  message?: string;
}

export default function IntegrityPage() {
  const [status, setStatus] = useState<IntegrityStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/dcl-status", { cache: "no-store" });
        if (!res.ok) {
          throw new Error(`Failed: ${res.status}`);
        }
        const payload = (await res.json()) as IntegrityStatus;
        setStatus(payload);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="p-6 text-sm text-token-secondary">Loading integrity status...</div>;
  }

  if (error || !status) {
    return (
      <div className="p-6">
        <div className="rounded-xl border border-token-border-default bg-token-elevated p-4">
          <p className="text-sm text-token-danger">Failed to load DCL integrity status.</p>
          <p className="mt-2 text-xs text-token-secondary">{error ?? "Unknown error"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-lg font-semibold text-token-primary">Deterministic Commitment Layer</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-token-border-default bg-token-elevated p-4">
          <p className="text-xs text-token-secondary uppercase tracking-wide">Packets With Commits</p>
          <p className="mt-2 text-2xl font-semibold">{status.packet_count}</p>
        </div>
        <div className="rounded-xl border border-token-border-default bg-token-elevated p-4">
          <p className="text-xs text-token-secondary uppercase tracking-wide">Total Commits</p>
          <p className="mt-2 text-2xl font-semibold">{status.commit_count}</p>
        </div>
        <div className="rounded-xl border border-token-border-default bg-token-elevated p-4">
          <p className="text-xs text-token-secondary uppercase tracking-wide">Project Checkpoints</p>
          <p className="mt-2 text-2xl font-semibold">{status.checkpoint_count}</p>
        </div>
      </div>
      <div className="rounded-xl border border-token-border-default bg-token-elevated p-4">
        <p className="text-sm text-token-secondary">
          Use CLI verification for chain integrity:
          <code className="ml-2">python3 .governance/wbs_cli.py verify --all</code>
        </p>
      </div>
    </div>
  );
}

