"use client";
import { StatusBadge } from "./StatusBadge";
import { Card } from "../ui/card";

interface Packet {
  id: string;
  wbs_ref: string;
  title: string;
  scope?: string;
  status: string;
  assigned_to?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  last_heartbeat_at?: string | null;
  notes?: string | null;
  preflight?: Record<string, unknown> | null;
  review?: Record<string, unknown> | null;
  context_attestation?: string[] | null;
}

interface PacketViewerProps {
  packet: Packet;
  onClose?: () => void;
}

export function PacketViewer({ packet, onClose }: PacketViewerProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="font-mono text-sm text-token-link font-semibold">{packet.wbs_ref}</span>
          <h3 className="text-lg font-semibold mt-1">{packet.title}</h3>
        </div>
        {onClose && <button onClick={onClose} className="text-token-tertiary hover:text-token-primary">&times;</button>}
      </div>
      <div className="flex gap-3">
        <StatusBadge status={packet.status} />
        {packet.assigned_to && <span className="text-sm text-token-secondary">Assigned: {packet.assigned_to}</span>}
      </div>
      {packet.last_heartbeat_at && (
        <Card>
          <h4 className="text-xs uppercase text-token-tertiary mb-1">Telemetry</h4>
          <p className="text-sm text-token-secondary">Last heartbeat: {packet.last_heartbeat_at}</p>
        </Card>
      )}
      {packet.context_attestation && packet.context_attestation.length > 0 && (
        <Card>
          <h4 className="text-xs uppercase text-token-tertiary mb-1">Context Attestation</h4>
          <p className="text-sm text-token-secondary">{packet.context_attestation.join(", ")}</p>
        </Card>
      )}
      {packet.preflight && (
        <Card>
          <h4 className="text-xs uppercase text-token-tertiary mb-1">Preflight</h4>
          <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(packet.preflight, null, 2)}</pre>
        </Card>
      )}
      {packet.review && (
        <Card>
          <h4 className="text-xs uppercase text-token-tertiary mb-1">Review</h4>
          <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(packet.review, null, 2)}</pre>
        </Card>
      )}
      {packet.scope && <Card><p className="text-sm text-token-secondary">{packet.scope}</p></Card>}
      {packet.notes && <Card><h4 className="text-xs uppercase text-token-tertiary mb-1">Notes</h4><p className="text-sm">{packet.notes}</p></Card>}
    </div>
  );
}
