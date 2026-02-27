/**
 * WBS grid column definitions and visual configuration.
 * Migrated from app/src/ui/wbsGridConfig.ts for Next.js template library.
 */

import type { WbsPacketRow } from "./types";

export const STATUS_HEATMAP_COLORS: Record<WbsPacketRow["status"], string> = {
  pending: "#8b8b8b",
  in_progress: "#2f80ed",
  done: "#27ae60",
  failed: "#eb5757",
  blocked: "#f2994a",
};

export const WBS_GRID_COLUMNS = [
  { field: "wbsRef", headerName: "WBS Ref", width: 120 },
  { field: "title", headerName: "Title", flex: 2 },
  { field: "status", headerName: "Status", width: 130 },
  { field: "owner", headerName: "Owner", width: 140 },
  { field: "priority", headerName: "Priority", width: 120 },
  { field: "blockedByCount", headerName: "Blocked By", width: 130 },
];

export function buildQuickFilterValue(row: WbsPacketRow): string {
  return [row.wbsRef, row.title, row.owner || "", row.status, row.priority].join(" ").toLowerCase();
}
