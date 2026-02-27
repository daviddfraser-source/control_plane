export type OpsPacketStatus = "pending" | "in_progress" | "done" | "failed" | "blocked";

export interface OpsPacket {
  id: string;
  wbs_ref: string;
  title: string;
  scope: string;
  status: OpsPacketStatus;
  assigned_to?: string;
  notes?: string;
}

interface OpsEdge {
  from: string;
  to: string;
}

const OPS_PACKETS: OpsPacket[] = [
  {
    id: "UX-101",
    wbs_ref: "1.1",
    title: "Navigation foundation",
    scope: "Primary shell navigation and responsive behavior",
    status: "done",
    assigned_to: "frontend",
    notes: "Shipped in sprint 1.",
  },
  {
    id: "UX-102",
    wbs_ref: "1.2",
    title: "Dashboard instrumentation",
    scope: "Surface core KPI cards and dependency health graph",
    status: "in_progress",
    assigned_to: "frontend",
    notes: "Finishing data wiring and accessibility pass.",
  },
  {
    id: "UX-103",
    wbs_ref: "1.3",
    title: "Marketplace catalog",
    scope: "Curated UI pattern library and preview routes",
    status: "done",
    assigned_to: "design-system",
    notes: "Catalog released and linked in workspace switcher.",
  },
  {
    id: "UX-104",
    wbs_ref: "1.4",
    title: "Approval workflow UI",
    scope: "Task approvals, reviewer state, and escalation flow",
    status: "pending",
  },
  {
    id: "UX-105",
    wbs_ref: "1.5",
    title: "Incident response board",
    scope: "Operational timeline and SLA compliance controls",
    status: "blocked",
    notes: "Waiting on backend event schema handoff.",
  },
];

const OPS_EDGES: OpsEdge[] = [
  { from: "UX-101", to: "UX-102" },
  { from: "UX-101", to: "UX-103" },
  { from: "UX-102", to: "UX-104" },
  { from: "UX-104", to: "UX-105" },
];

export function getDashboardSnapshot() {
  const counts = {
    pending: 0,
    in_progress: 0,
    done: 0,
    failed: 0,
    blocked: 0,
  };

  for (const packet of OPS_PACKETS) {
    counts[packet.status] += 1;
  }

  return {
    counts,
    total: OPS_PACKETS.length,
    nodes: OPS_PACKETS.map((packet) => ({
      id: packet.id,
      title: packet.title,
      wbs_ref: packet.wbs_ref,
      status: packet.status,
    })),
    edges: OPS_EDGES,
  };
}

export function getOpsPacketById(packetId: string): OpsPacket | null {
  return OPS_PACKETS.find((packet) => packet.id === packetId) ?? null;
}
