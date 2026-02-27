"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchStatus, type StatusResponse, type StatusPacket } from "@/lib/governance/api-client";
import { StatusBadge } from "@/components/governance/StatusBadge";

export default function WbsViewerPage() {
    const router = useRouter();
    const [status, setStatus] = useState<StatusResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [source, setSource] = useState<"governance-api" | "local-dev-wbs">("governance-api");

    useEffect(() => {
        const load = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await fetchStatus();
                setStatus(data);
                setSource("governance-api");
            } catch (err) {
                try {
                    const fallbackResponse = await fetch("/api/dev-wbs", { cache: "no-store" });
                    if (!fallbackResponse.ok) {
                        throw new Error(`Fallback load failed: ${fallbackResponse.status}`);
                    }
                    const fallbackData = (await fallbackResponse.json()) as StatusResponse;
                    setStatus(fallbackData);
                    setSource("local-dev-wbs");
                    setError(err instanceof Error ? err.message : "Failed to load WBS data");
                } catch (fallbackErr) {
                    setError(
                        fallbackErr instanceof Error
                            ? fallbackErr.message
                            : err instanceof Error
                                ? err.message
                                : "Failed to load WBS data",
                    );
                }
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const legacyViewerUrl =
        typeof window !== "undefined"
            ? process.env.NEXT_PUBLIC_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8080/`
            : `http://127.0.0.1:${process.env.NEXT_PUBLIC_API_PORT ?? "8080"}/`;

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-token-primary mx-auto mb-4"></div>
                    <p className="text-token-secondary">Loading WBS...</p>
                </div>
            </div>
        );
    }

    if (error || !status) {
        return (
            <div className="h-full flex items-center justify-center p-6">
                <div className="max-w-xl w-full bg-token-elevated border border-token-border-default rounded-xl p-6">
                    <h1 className="text-lg font-semibold text-token-primary mb-2">WBS Viewer</h1>
                    <p className="text-sm text-token-secondary mb-4">
                        Could not load WBS state from the governance API.
                    </p>
                    <p className="text-sm text-token-danger mb-4">{error ?? "Unknown error"}</p>
                    {error?.toLowerCase().includes("authentication required") && (
                        <p className="text-xs text-token-secondary mb-4">
                            Sign in from <a href="/dev/settings" className="underline text-token-link">Control Plane Settings</a> and retry.
                        </p>
                    )}
                    <div className="flex gap-2">
                        <button
                            onClick={() => window.location.reload()}
                            className="px-3 py-1.5 text-sm bg-token-primary text-white rounded border border-token-border-default"
                        >
                            Retry
                        </button>
                        <a
                            href={legacyViewerUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3 py-1.5 text-sm bg-token-inset text-token-primary rounded border border-token-border-default"
                        >
                            Open Legacy Viewer ↗
                        </a>
                    </div>
                </div>
            </div>
        );
    }

    const totalPackets = status.areas.reduce((sum, area) => sum + area.packets.length, 0);

    return (
        <div className="h-full flex flex-col bg-token-canvas overflow-auto">
            <div className="bg-token-elevated border-b border-token-border-default px-4 py-3 flex items-center justify-between gap-3">
                <div>
                    <h1 className="text-base font-semibold text-token-primary">WBS Viewer</h1>
                    <p className="text-xs text-token-secondary">
                        {status.areas.length} areas · {totalPackets} packets
                    </p>
                    {source === "local-dev-wbs" && (
                        <p className="text-xs text-token-warning mt-1">
                            Showing local dev WBS snapshot (read-only fallback).
                        </p>
                    )}
                </div>
                <button
                    onClick={() => window.location.reload()}
                    className="px-3 py-1.5 text-xs bg-token-inset text-token-primary rounded border border-token-border-default hover:border-token-border-strong transition-colors"
                >
                    ↻ Refresh
                </button>
            </div>
            <div className="p-4 space-y-4">
                {status.areas.length === 0 && (
                    <div className="bg-token-elevated border border-token-border-default rounded-lg p-4 text-sm text-token-secondary">
                        No WBS areas were returned. Try refreshing, then verify `.governance/wbs.json` exists.
                    </div>
                )}
                {status.areas.map((area) => (
                    <section key={area.id} className="bg-token-elevated rounded-lg border border-token-border-default">
                        <div className="px-4 py-3 border-b border-token-border-default">
                            <div className="flex items-center justify-between">
                                <h2 className="text-sm font-semibold text-token-primary">
                                    [{area.id}] {area.title}
                                </h2>
                                <span className="text-xs text-token-secondary">{area.packets.length} packets</span>
                            </div>
                            {area.description && (
                                <p className="text-xs text-token-secondary mt-1">{area.description}</p>
                            )}
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-token-secondary text-token-secondary">
                                        <th className="text-left px-4 py-2 text-xs uppercase tracking-wide">WBS</th>
                                        <th className="text-left px-4 py-2 text-xs uppercase tracking-wide">Packet</th>
                                        <th className="text-left px-4 py-2 text-xs uppercase tracking-wide">Status</th>
                                        <th className="text-left px-4 py-2 text-xs uppercase tracking-wide">Owner</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {area.packets.map((packet: StatusPacket) => (
                                        <tr
                                            key={packet.id}
                                            className="border-t border-token-border-default cursor-pointer hover:bg-token-inset"
                                            onClick={() => router.push(`/dev/packets/${packet.id}`)}
                                            title={`Open packet ${packet.id}`}
                                        >
                                            <td className="px-4 py-2 font-mono text-token-link">{packet.wbs_ref}</td>
                                            <td className="px-4 py-2">
                                                <div className="font-medium text-token-primary">{packet.title}</div>
                                                <div className="text-xs text-token-secondary">{packet.id}</div>
                                            </td>
                                            <td className="px-4 py-2">
                                                <StatusBadge status={packet.status} />
                                            </td>
                                            <td className="px-4 py-2 text-token-secondary">{packet.assigned_to ?? "-"}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                ))}
            </div>
        </div>
    );
}
