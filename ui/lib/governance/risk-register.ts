/**
 * Risk register grid: filtering and navigation helpers.
 * Migrated from app/src/ui/riskRegister.ts for Next.js template library.
 */

export interface RiskGridRow {
  risk_id: string;
  packet_id: string;
  status: string;
  severity: string;
  escalation_level: string;
}

export interface RiskFilter {
  status?: string;
  packetId?: string;
}

export function filterRiskRows(rows: RiskGridRow[], filter: RiskFilter): RiskGridRow[] {
  return rows.filter((row) => {
    if (filter.status && row.status !== filter.status) {
      return false;
    }
    if (filter.packetId && row.packet_id !== filter.packetId) {
      return false;
    }
    return true;
  });
}

export function linkedPacketPath(packetId: string): string {
  return `/packets/${packetId}`;
}
