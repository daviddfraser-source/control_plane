import { NextResponse } from "next/server";
import { accessSync, promises as fs } from "node:fs";
import path from "node:path";

interface RuntimePacketState {
  status?: string;
  assigned_to?: string | null;
  notes?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  last_heartbeat_at?: string | null;
  context_attestation?: string[] | null;
  preflight?: Record<string, unknown> | null;
  review?: Record<string, unknown> | null;
}

function findRepoRoot(): string {
  let current = process.cwd();
  for (let i = 0; i < 8; i += 1) {
    const candidate = path.join(current, ".governance", "wbs.json");
    try {
      accessSync(candidate);
      return current;
    } catch {
      const parent = path.dirname(current);
      if (parent === current) break;
      current = parent;
    }
  }
  return path.resolve(process.cwd(), "..", "..");
}

export async function GET() {
  try {
    const root = findRepoRoot();
    const wbsPath = path.join(root, ".governance", "wbs.json");
    const statePath = path.join(root, ".governance", "wbs-state.json");

    const [wbsRaw, stateRaw] = await Promise.all([
      fs.readFile(wbsPath, "utf-8"),
      fs.readFile(statePath, "utf-8"),
    ]);

    const wbs = JSON.parse(wbsRaw);
    const state = JSON.parse(stateRaw);
    const packetStateMap: Record<string, RuntimePacketState> = state?.packets ?? {};

    const packets = Array.isArray(wbs?.packets) ? wbs.packets : [];
    const areas = (Array.isArray(wbs?.work_areas) ? wbs.work_areas : []).map((area: { id: string; title: string; description?: string }) => {
      const areaPackets = packets
        .filter((packet: { area_id?: string }) => packet.area_id === area.id)
        .map((packet: { id: string; wbs_ref?: string; title?: string; scope?: string }) => {
          const runtime = packetStateMap[packet.id] ?? {};
          return {
            id: packet.id,
            wbs_ref: packet.wbs_ref ?? "",
            title: packet.title ?? "",
            scope: packet.scope ?? "",
            status: runtime.status ?? "pending",
            assigned_to: runtime.assigned_to ?? null,
            notes: runtime.notes ?? null,
            started_at: runtime.started_at ?? null,
            completed_at: runtime.completed_at ?? null,
            last_heartbeat_at: runtime.last_heartbeat_at ?? null,
            context_attestation: runtime.context_attestation ?? null,
            preflight: runtime.preflight ?? null,
            review: runtime.review ?? null,
          };
        });
      return {
        id: area.id,
        title: area.title,
        description: area.description ?? "",
        packets: areaPackets,
      };
    });

    return NextResponse.json({
      metadata: { source: "local-dev-wbs" },
      areas,
      dependencies: wbs?.dependencies ?? {},
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        message: error instanceof Error ? error.message : "Failed to load local WBS files",
      },
      { status: 500 },
    );
  }
}
