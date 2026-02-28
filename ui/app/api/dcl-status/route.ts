import { NextResponse } from "next/server";
import { accessSync, promises as fs } from "node:fs";
import path from "node:path";

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
    const dclPackets = path.join(root, ".governance", "dcl", "packets");
    const checkpointDir = path.join(root, ".governance", "dcl", "project-checkpoints");

    let packetCount = 0;
    let commitCount = 0;
    try {
      const packets = await fs.readdir(dclPackets);
      packetCount = packets.length;
      for (const packet of packets) {
        const commitsDir = path.join(dclPackets, packet, "commits");
        try {
          const commits = await fs.readdir(commitsDir);
          commitCount += commits.filter((item) => item.endsWith(".json")).length;
        } catch {
          // ignore packet without commits
        }
      }
    } catch {
      // no dcl packet directory yet
    }

    let checkpoints = 0;
    try {
      const rows = await fs.readdir(checkpointDir);
      checkpoints = rows.filter((item) => item.endsWith(".json")).length;
    } catch {
      // no checkpoints yet
    }

    return NextResponse.json({
      ok: true,
      packet_count: packetCount,
      commit_count: commitCount,
      checkpoint_count: checkpoints,
    });
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        message: error instanceof Error ? error.message : "Failed to read DCL status",
      },
      { status: 500 },
    );
  }
}

