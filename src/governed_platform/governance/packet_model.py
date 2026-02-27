from dataclasses import dataclass
from datetime import datetime
from typing import Optional


PacketStatus = str


@dataclass
class PacketRuntimeState:
    packet_id: str
    status: PacketStatus = "pending"
    assigned_to: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: Optional[str] = None

    def mark_started(self, agent: str):
        self.status = "in_progress"
        self.assigned_to = agent
        self.started_at = datetime.now().isoformat()

    def mark_done(self, notes: str):
        self.status = "done"
        self.completed_at = datetime.now().isoformat()
        self.notes = notes

    def mark_failed(self, reason: str):
        self.status = "failed"
        self.completed_at = datetime.now().isoformat()
        self.notes = reason
