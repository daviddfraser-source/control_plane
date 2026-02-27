/**
 * WBS grid inline editing and bulk action logic.
 * Migrated from app/src/ui/wbsGridActions.ts for Next.js template library.
 */

import type { RolePermissions, WbsPacketRow } from "./types";

export interface BulkActionRequest {
  rowIds: string[];
  field: "owner" | "priority" | "status";
  value: string;
}

export function canEditCell(permissions: RolePermissions): boolean {
  return permissions.canView && permissions.canEdit;
}

export function applyInlineEdit(
  row: WbsPacketRow,
  field: "owner" | "priority" | "status",
  value: string,
  permissions: RolePermissions,
): WbsPacketRow {
  if (!canEditCell(permissions)) {
    throw new Error("unauthorized_edit");
  }
  return { ...row, [field]: value } as WbsPacketRow;
}

export function applyBulkAction(
  rows: WbsPacketRow[],
  request: BulkActionRequest,
  permissions: RolePermissions,
): WbsPacketRow[] {
  if (!permissions.canBulkEdit) {
    throw new Error("unauthorized_bulk_edit");
  }
  const target = new Set(request.rowIds);
  return rows.map((row) => {
    if (!target.has(row.id)) {
      return row;
    }
    return { ...row, [request.field]: request.value } as WbsPacketRow;
  });
}
