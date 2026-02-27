"use client";

import { useEffect, useState } from "react";
import { AuditTable } from "@/components/governance/AuditTable";
import { fetchLog, type LogEntry } from "@/lib/governance/api-client";

export default function AuditPage() {
    const [entries, setEntries] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [limit, setLimit] = useState(50);

    useEffect(() => {
        const load = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await fetchLog(limit);
                setEntries(data.log);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load audit log");
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [limit]);

    return (
        <div className="h-full flex flex-col">
            <div className="bg-token-elevated border-b border-token-border-default p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold text-token-primary">Audit Log</h1>
                        <p className="text-sm text-token-secondary">{entries.length} recent events</p>
                    </div>
                    <button
                        onClick={() => window.location.reload()}
                        disabled={loading}
                        className="px-3 py-1.5 text-sm bg-token-inset text-token-primary rounded border border-token-border-default hover:border-token-border-strong transition-colors disabled:opacity-50"
                    >
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
                {loading && entries.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-token-primary"></div>
                    </div>
                ) : (
                    <>
                        <AuditTable entries={entries} />
                        {entries.length >= limit && (
                            <div className="mt-4 text-center">
                                <button
                                    onClick={() => setLimit(prev => prev + 50)}
                                    disabled={loading}
                                    className="px-4 py-2 text-sm bg-token-primary text-white rounded-md hover:bg-opacity-90 transition-colors disabled:opacity-50"
                                >
                                    {loading ? "Loading..." : "Load More"}
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
