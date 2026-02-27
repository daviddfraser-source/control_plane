/**
 * Audit log viewer: filter construction and row types.
 * Migrated from app/src/ui/auditViewer.ts for Next.js template library.
 */

export interface AuditFilter {
  tenantId?: string;
  actor?: string;
  packetId?: string;
  startDate?: string;
  endDate?: string;
  page: number;
  pageSize: number;
}

export interface AuditRow {
  entry_id: string;
  tenant_id: string;
  actor: string;
  packet_id: string;
  event_type: string;
  created_at: string;
}

export function buildAuditQueryParams(filter: AuditFilter): Record<string, string> {
  const out: Record<string, string> = {
    page: String(filter.page),
    page_size: String(filter.pageSize),
  };
  if (filter.tenantId) out.tenant_id = filter.tenantId;
  if (filter.actor) out.actor = filter.actor;
  if (filter.packetId) out.packet_id = filter.packetId;
  if (filter.startDate) out.start_date = filter.startDate;
  if (filter.endDate) out.end_date = filter.endDate;
  return out;
}
