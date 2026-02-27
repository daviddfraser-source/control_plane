"use client";

import { useEffect, useState } from "react";
import { fetchDepsGraph, type DepsGraphResponse } from "@/lib/governance/api-client";
import { DependencyGraph } from "@/components/governance/DependencyGraph";

export default function GraphPage() {
    const [graph, setGraph] = useState<DepsGraphResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [highlightCriticalPath, setHighlightCriticalPath] = useState(false);

    useEffect(() => {
        const load = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await fetchDepsGraph();
                setGraph(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load dependency graph");
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-token-primary mx-auto mb-4"></div>
                    <p className="text-token-secondary">Loading dependency graph...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md">
                    <p className="text-token-danger mb-2">⚠️ Error Loading Graph</p>
                    <p className="text-sm text-token-secondary">{error}</p>
                    <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-token-primary text-white rounded-md">Retry</button>
                </div>
            </div>
        );
    }

    const nodeCount = graph?.nodes.length || 0;
    const edgeCount = graph?.edges.length || 0;

    return (
        <div className="h-full flex flex-col">
            <div className="bg-token-elevated border-b border-token-border-default p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold text-token-primary">Dependency Graph</h1>
                        <p className="text-sm text-token-secondary">{nodeCount} nodes, {edgeCount} dependencies</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <label className="flex items-center gap-2 text-sm text-token-secondary">
                            <input
                                type="checkbox"
                                checked={highlightCriticalPath}
                                onChange={(e) => setHighlightCriticalPath(e.target.checked)}
                                className="rounded border-token-border-default"
                            />
                            Highlight Critical Path
                        </label>
                        <button onClick={() => window.location.reload()} className="px-3 py-1.5 text-sm bg-token-inset text-token-primary rounded border border-token-border-default hover:border-token-border-strong transition-colors">
                            ↻ Refresh
                        </button>
                    </div>
                </div>
            </div>
            <div className="flex-1 overflow-hidden p-4">
                {graph && (
                    <div className="h-full bg-token-elevated rounded-lg border border-token-border-default p-4">
                        <DependencyGraph nodes={graph.nodes} edges={graph.edges} highlightCriticalPath={highlightCriticalPath} />
                    </div>
                )}
            </div>
            <div className="bg-token-elevated border-t border-token-border-default p-4">
                <div className="flex items-center gap-6 text-xs">
                    {[["bg-green-500", "Done"], ["bg-blue-500", "In Progress"], ["bg-gray-500", "Pending"], ["bg-red-500", "Failed"], ["bg-yellow-500", "Blocked"]].map(([color, label]) => (
                        <div key={label} className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${color}`}></div>
                            <span className="text-token-secondary">{label}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
