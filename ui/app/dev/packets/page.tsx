"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { WorkspaceView } from "@/components/governance/WorkspaceView";
import { fetchStatus, type StatusResponse, type StatusPacket } from "@/lib/governance/api-client";

export default function PacketsPage() {
    const router = useRouter();
    const [status, setStatus] = useState<StatusResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<"table" | "kanban" | "tree" | "graph">("table");
    const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await fetchStatus();
                setStatus(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load packets");
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-token-primary mx-auto mb-4"></div>
                    <p className="text-token-secondary">Loading packets...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md">
                    <p className="text-token-danger mb-2">⚠️ Error Loading Packets</p>
                    <p className="text-sm text-token-secondary">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-4 px-4 py-2 bg-token-primary text-white rounded-md hover:bg-opacity-90 transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    const allPackets: StatusPacket[] = status?.areas.flatMap(area => area.packets) || [];
    const filteredPackets = searchQuery
        ? allPackets.filter(
            p =>
                p.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                p.wbs_ref.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : allPackets;

    const handlePacketClick = (packetId: string) => {
        router.push(`/dev/packets/${packetId}`);
    };

    return (
        <div className="h-full flex flex-col">
            <div className="bg-token-elevated border-b border-token-border-default p-4">
                <div className="flex items-center justify-between gap-4 mb-4">
                    <div>
                        <h1 className="text-xl font-bold text-token-primary">Packet Manager</h1>
                        <p className="text-sm text-token-secondary">{filteredPackets.length} packets</p>
                    </div>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-3 py-1.5 text-sm bg-token-inset text-token-primary rounded border border-token-border-default hover:border-token-border-strong transition-colors"
                    >
                        ↻ Refresh
                    </button>
                </div>
                <div className="flex items-center gap-3">
                    <input
                        type="text"
                        placeholder="Search packets..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="flex-1 px-3 py-2 text-sm bg-token-canvas border border-token-border-default rounded-md focus:outline-none focus:ring-2 focus:ring-token-primary focus:border-transparent"
                    />
                    <div className="flex items-center gap-1 bg-token-inset rounded-md p-1 border border-token-border-default">
                        {(["table", "kanban", "tree", "graph"] as const).map((mode) => (
                            <button
                                key={mode}
                                onClick={() => setViewMode(mode)}
                                className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${viewMode === mode
                                        ? "bg-token-primary text-white"
                                        : "text-token-secondary hover:text-token-primary"
                                    }`}
                            >
                                {mode.charAt(0).toUpperCase() + mode.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
                <WorkspaceView
                    mode={viewMode}
                    packets={filteredPackets}
                    onPacketClick={handlePacketClick}
                />
            </div>
        </div>
    );
}
