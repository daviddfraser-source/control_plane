"use client";

import { KanbanBoard } from "./KanbanBoard";
import { TreeView } from "./TreeView";
import { DependencyGraph } from "./DependencyGraph";
import { StatusBadge } from "./StatusBadge";

type ViewMode = "table" | "kanban" | "tree" | "graph";

interface PacketRow {
  id: string;
  wbs_ref: string;
  title: string;
  status: string;
  assigned_to?: string | null;
}

interface WorkspaceViewProps {
  mode: ViewMode;
  packets: PacketRow[];
  onPacketClick?: (id: string) => void;
}

export function WorkspaceView({ mode, packets, onPacketClick }: WorkspaceViewProps) {
  if (mode === "kanban") {
    return <KanbanBoard packets={packets} onPacketClick={onPacketClick} />;
  }

  if (mode === "tree") {
    const nodes = packets.map((packet) => ({
      id: packet.id,
      label: `${packet.wbs_ref} ${packet.title}`,
      status: packet.status,
    }));
    return <TreeView nodes={nodes} onNodeClick={onPacketClick} />;
  }

  if (mode === "graph") {
    const nodes = packets.map((packet) => ({
      id: packet.id,
      title: packet.title,
      wbs_ref: packet.wbs_ref,
      status: packet.status,
    }));
    return <DependencyGraph nodes={nodes} edges={[]} />;
  }

  return (
    <div className="border border-token-default rounded-[var(--radius-xl)] overflow-hidden bg-token-surface">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-token-secondary text-token-secondary">
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">WBS</th>
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">Title</th>
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">Status</th>
            <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-wide">Owner</th>
          </tr>
        </thead>
        <tbody>
          {packets.map((packet) => (
            <tr
              key={packet.id}
              className="border-t border-token-muted hover:bg-token-inset cursor-pointer"
              onClick={() => onPacketClick?.(packet.id)}
            >
              <td className="px-4 py-2.5 font-mono text-token-link">{packet.wbs_ref}</td>
              <td className="px-4 py-2.5 font-medium">{packet.title}</td>
              <td className="px-4 py-2.5"><StatusBadge status={packet.status} /></td>
              <td className="px-4 py-2.5 text-token-tertiary">{packet.assigned_to || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {packets.length === 0 && <div className="text-center py-8 text-sm text-token-tertiary">No packets</div>}
    </div>
  );
}
