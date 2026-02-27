"use client";

import { useEffect, useState } from "react";
import { RiskTable } from "@/components/governance/RiskTable";
import { fetchStatus } from "@/lib/governance/api-client";

interface Risk {
    id: string; packetId: string; title: string;
    severity: "low" | "medium" | "high" | "critical";
    likelihood: "low" | "medium" | "high";
    impact: string; mitigation: string;
    status: "open" | "mitigated" | "accepted";
}

export default function RisksPage() {
    const [risks, setRisks] = useState<Risk[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                setLoading(true);
                setError(null);
                const statusData = await fetchStatus();
                const extracted: Risk[] = [];
                statusData.areas.forEach((area) => {
                    area.packets.forEach((packet) => {
                        if (packet.status === "failed") {
                            extracted.push({
                                id: `risk-${packet.id}`, packetId: packet.id,
                                title: `Packet ${packet.wbs_ref} failed`,
                                severity: "high", likelihood: "high",
                                impact: packet.notes || "Packet execution failed",
                                mitigation: "Review failure notes and restart packet",
                                status: "open",
                            });
                        }
                    });
                });
                setRisks(extracted);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load risks");
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-token-primary"></div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            <div className="bg-token-elevated border-b border-token-border-default p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold text-token-primary">Risk Register</h1>
                        <p className="text-sm text-token-secondary">{risks.length} identified risks</p>
                    </div>
                    <button onClick={() => window.location.reload()} className="px-3 py-1.5 text-sm bg-token-inset text-token-primary rounded border border-token-border-default hover:border-token-border-strong transition-colors">
                        ↻ Refresh
                    </button>
                </div>
            </div>
            {error && (
                <div className="m-4 p-4 bg-token-danger-muted border border-token-danger rounded-md">
                    <p className="text-sm text-token-danger">⚠️ {error}</p>
                </div>
            )}
            <div className="flex-1 overflow-auto p-4">
                {risks.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                            <p className="text-2xl mb-2">✅</p>
                            <p className="text-token-secondary">No active risks identified</p>
                            <p className="text-sm text-token-tertiary mt-1">All packets are executing within acceptable parameters</p>
                        </div>
                    </div>
                ) : (
                    <RiskTable risks={risks} />
                )}
            </div>
        </div>
    );
}
