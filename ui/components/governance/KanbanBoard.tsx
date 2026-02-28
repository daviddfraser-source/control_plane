"use client";
import { StatusBadge } from "./StatusBadge";

interface Packet {
  id: string;
  title: string;
  status: string;
  assigned_to?: string | null;
}

interface KanbanBoardProps {
  packets: Packet[];
  onPacketClick?: (id: string) => void;
}

const columns = ["pending", "preflight", "in_progress", "stalled", "review", "escalated", "done", "failed"];
const columnLabels: Record<string, string> = {
  pending: "Pending",
  preflight: "Preflight",
  in_progress: "In Progress",
  stalled: "Stalled",
  review: "Review",
  escalated: "Escalated",
  done: "Done",
  failed: "Failed",
};

export function KanbanBoard({ packets, onPacketClick }: KanbanBoardProps) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map(col => {
        const items = packets.filter(p => p.status === col);
        return (
          <div key={col} className="flex-shrink-0 w-[280px]">
            <div className="text-xs font-semibold uppercase tracking-wide text-token-tertiary mb-3 flex items-center gap-2">
              {columnLabels[col]} <span className="bg-token-inset px-1.5 py-0.5 rounded-full text-[10px]">{items.length}</span>
            </div>
            <div className="space-y-2">
              {items.map(p => (
                <div
                  key={p.id}
                  className="bg-token-surface border border-token-default rounded-[var(--radius-lg)] p-3 cursor-pointer hover:shadow-token-sm transition-shadow"
                  onClick={() => onPacketClick?.(p.id)}
                >
                  <div className="text-sm font-medium">{p.title}</div>
                  <div className="flex items-center justify-between mt-2">
                    <StatusBadge status={p.status} />
                    {p.assigned_to && <span className="text-xs text-token-tertiary">{p.assigned_to}</span>}
                  </div>
                </div>
              ))}
              {items.length === 0 && <div className="text-xs text-token-tertiary text-center py-8">No items</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
