from datetime import datetime
from pathlib import Path
import re
from typing import Dict, Any, Tuple, List

from governed_platform.governance.interfaces import GovernanceInterface
from governed_platform.governance.file_lock import file_lock
from governed_platform.governance.log_integrity import (
    LOG_MODE_HASH_CHAIN,
    build_log_entry,
    normalize_log_mode,
    verify_log_integrity,
)
from governed_platform.governance.state_manager import StateManager
from governed_platform.governance.status import normalize_runtime_status
from governed_platform.governance.supervisor import (
    DeterministicSupervisor,
    TransitionRequest,
    SupervisorInterface,
)


class GovernanceEngine(GovernanceInterface):
    """Governance lifecycle engine detached from CLI concerns."""

    def __init__(self, definition: Dict[str, Any], state_manager: StateManager, supervisor: SupervisorInterface = None):
        self.definition = definition
        self.state_manager = state_manager
        self.supervisor = supervisor or DeterministicSupervisor()

    def _load(self) -> Dict[str, Any]:
        return self.state_manager.load()

    def _save(self, state: Dict[str, Any]) -> None:
        self.state_manager.save(state)

    def _deps_met(self, state: Dict[str, Any], packet_id: str) -> Tuple[bool, str]:
        deps = self.definition.get("dependencies", {}).get(packet_id, [])
        for dep_id in deps:
            dep_state = state.get("packets", {}).get(dep_id, {})
            if normalize_runtime_status(dep_state.get("status")) != "done":
                return False, dep_id
        return True, ""

    def _log(self, state: Dict[str, Any], packet_id: str, event: str, agent: str = None, notes: str = None):
        log_entries = state.setdefault("log", [])
        mode = normalize_log_mode(state.get("log_integrity_mode", "plain"))
        timestamp = datetime.now().isoformat()

        prev_hash = ""
        hash_index = 1
        if mode == LOG_MODE_HASH_CHAIN:
            hashed_entries = [e for e in log_entries if isinstance(e, dict) and e.get("hash")]
            if hashed_entries:
                prev_hash = hashed_entries[-1].get("hash", "") or ""
                hash_index = len(hashed_entries) + 1

        log_entries.append(
            build_log_entry(
                packet_id=packet_id,
                event=event,
                agent=agent,
                notes=notes,
                timestamp=timestamp,
                mode=mode,
                previous_hash=prev_hash,
                hash_index=hash_index,
            )
        )

    def _approve(
        self,
        action: str,
        packet_id: str,
        agent: str = None,
        notes: str = None,
        required_capabilities: List[str] = None,
    ) -> Tuple[bool, str]:
        req = TransitionRequest(
            packet_id=packet_id,
            action=action,
            agent=agent,
            notes=notes,
            required_capabilities=required_capabilities,
        )
        return self.supervisor.approve(req)

    def _active_handover(self, packet_state: Dict[str, Any]) -> Dict[str, Any]:
        for item in reversed(packet_state.get("handovers", [])):
            if isinstance(item, dict) and item.get("active"):
                return item
        return {}

    def _find_packet_definition(self, packet_id: str) -> Dict[str, Any]:
        for pkt in self.definition.get("packets", []):
            if pkt.get("id") == packet_id:
                return pkt
        return {}

    def _collect_text_values(self, value: Any, out: List[str]) -> None:
        if isinstance(value, str):
            out.append(value)
            return
        if isinstance(value, list):
            for item in value:
                self._collect_text_values(item, out)
            return
        if isinstance(value, dict):
            for item in value.values():
                self._collect_text_values(item, out)

    def _extract_file_manifest(self, *texts: str) -> List[Dict[str, Any]]:
        repo_root = Path.cwd().resolve()
        candidates = set()
        token_re = re.compile(r"[A-Za-z0-9_./-]+")
        allowed_ext = {
            ".md",
            ".txt",
            ".json",
            ".py",
            ".sh",
            ".yml",
            ".yaml",
            ".html",
            ".js",
            ".ts",
            ".tsx",
            ".csv",
            ".log",
        }
        for text in texts:
            if not text:
                continue
            for token in token_re.findall(text):
                token = token.strip(".,;:()[]{}<>\"'`")
                if token.startswith("http://") or token.startswith("https://"):
                    continue
                if token.startswith("."):
                    token = token.lstrip("./")
                if not token:
                    continue
                ext = Path(token).suffix.lower()
                if "/" not in token and ext not in allowed_ext:
                    continue
                candidates.add(token)

        out = []
        for rel in sorted(candidates):
            target = (repo_root / rel).resolve()
            exists = str(target).startswith(str(repo_root)) and target.is_file()
            out.append({"path": rel, "exists": bool(exists)})
        return out

    def _truncate_text(self, value: Any, max_bytes: int) -> Tuple[str, int]:
        text = str(value or "")
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text, 0
        trimmed = encoded[:max_bytes].decode("utf-8", errors="ignore")
        dropped = len(encoded) - len(trimmed.encode("utf-8"))
        return trimmed, dropped

    def claim(self, packet_id: str, agent: str) -> Tuple[bool, str]:
        packet_definition = self._find_packet_definition(packet_id)
        required_capabilities = []
        if packet_definition and isinstance(packet_definition.get("required_capabilities"), list):
            required_capabilities = packet_definition.get("required_capabilities", [])

        allowed, reason = self._approve(
            "claim",
            packet_id,
            agent=agent,
            required_capabilities=required_capabilities,
        )
        if not allowed:
            return False, reason

        # Hold the lock across load->validate->mutate->save so concurrent claims
        # cannot both observe "pending" and succeed.
        with file_lock(self.state_manager.state_path):
            state = self._load()
            if packet_id not in state.get("packets", {}):
                return False, f"Packet {packet_id} not found"
            pkt = state["packets"][packet_id]
            current_status = normalize_runtime_status(pkt.get("status"))
            if current_status != "pending":
                return False, f"Packet {packet_id} is {current_status}, not pending"
            ok, blocking = self._deps_met(state, packet_id)
            if not ok:
                return False, f"Blocked by {blocking} (not done yet)"
            pkt["status"] = "in_progress"
            pkt["assigned_to"] = agent
            pkt["started_at"] = datetime.now().isoformat()
            self._log(state, packet_id, "started", agent, f"Claimed by {agent}")
            if reason and reason != "approved":
                self._log(state, packet_id, "capability_warning", agent, reason)
            self.state_manager.save_without_lock(state)

        message = f"{packet_id} claimed by {agent}"
        if reason and reason != "approved":
            message += f" ({reason})"
        return True, message

    def done(self, packet_id: str, agent: str, notes: str = "") -> Tuple[bool, str]:
        allowed, reason = self._approve("done", packet_id, agent=agent, notes=notes)
        if not allowed:
            return False, reason
        state = self._load()
        if packet_id not in state.get("packets", {}):
            return False, f"Packet {packet_id} not found"
        pkt = state["packets"][packet_id]
        current_status = normalize_runtime_status(pkt.get("status"))
        if current_status != "in_progress":
            return False, f"Packet {packet_id} is {current_status}, not in_progress"
        if self._active_handover(pkt):
            return False, f"Packet {packet_id} has active handover; resume before done"
        pkt["status"] = "done"
        pkt["completed_at"] = datetime.now().isoformat()
        pkt["notes"] = notes
        self._log(state, packet_id, "completed", agent, notes)
        self._save(state)
        return True, f"{packet_id} marked done"

    def note(self, packet_id: str, agent: str, notes: str) -> Tuple[bool, str]:
        allowed, reason = self._approve("note", packet_id, agent=agent, notes=notes)
        if not allowed:
            return False, reason
        state = self._load()
        if packet_id not in state.get("packets", {}):
            return False, f"Packet {packet_id} not found"
        state["packets"][packet_id]["notes"] = notes
        self._log(state, packet_id, "noted", agent, notes)
        self._save(state)
        return True, f"{packet_id} notes updated"

    def fail(self, packet_id: str, agent: str, reason: str = "") -> Tuple[bool, str]:
        allowed, sup_reason = self._approve("fail", packet_id, agent=agent, notes=reason)
        if not allowed:
            return False, sup_reason
        state = self._load()
        if packet_id not in state.get("packets", {}):
            return False, f"Packet {packet_id} not found"
        pkt = state["packets"][packet_id]
        current_status = normalize_runtime_status(pkt.get("status"))
        if current_status not in ("pending", "in_progress"):
            return False, f"Packet {packet_id} is {current_status}, cannot fail"
        if self._active_handover(pkt):
            return False, f"Packet {packet_id} has active handover; resume before fail"
        pkt["status"] = "failed"
        pkt["completed_at"] = datetime.now().isoformat()
        pkt["notes"] = reason
        self._log(state, packet_id, "failed", agent, reason)
        deps = self.definition.get("dependencies", {})
        to_block = [pid for pid, dep_list in deps.items() if packet_id in dep_list]
        blocked = []
        while to_block:
            pid = to_block.pop(0)
            cur = state.get("packets", {}).get(pid, {})
            if normalize_runtime_status(cur.get("status")) in ("pending", "in_progress"):
                cur["status"] = "blocked"
                self._log(state, pid, "blocked", None, f"Blocked by {packet_id}")
                blocked.append(pid)
                to_block.extend(p for p, d in deps.items() if pid in d)
        self._save(state)
        suffix = f"; blocked: {', '.join(blocked)}" if blocked else ""
        return True, f"{packet_id} failed{suffix}"

    def reset(self, packet_id: str) -> Tuple[bool, str]:
        state = self._load()
        if packet_id not in state.get("packets", {}):
            return False, f"Packet {packet_id} not found"
        pkt = state["packets"][packet_id]
        current_status = normalize_runtime_status(pkt.get("status"))
        if current_status != "in_progress":
            return False, f"Packet {packet_id} is {current_status}, not in_progress"
        pkt["status"] = "pending"
        pkt["assigned_to"] = None
        pkt["started_at"] = None
        self._log(state, packet_id, "reset", None, None)
        self._save(state)
        return True, f"{packet_id} reset to pending"

    def handover(
        self,
        packet_id: str,
        agent: str,
        reason: str,
        progress_notes: str = "",
        files_modified: List[str] = None,
        remaining_work: List[str] = None,
        to_agent: str = None,
    ) -> Tuple[bool, str]:
        allowed, sup_reason = self._approve("handover", packet_id, agent=agent, notes=reason)
        if not allowed:
            return False, sup_reason

        state = self._load()
        if packet_id not in state.get("packets", {}):
            return False, f"Packet {packet_id} not found"
        pkt = state["packets"][packet_id]
        current_status = normalize_runtime_status(pkt.get("status"))
        if current_status != "in_progress":
            return False, f"Packet {packet_id} is {current_status}, not in_progress"
        current_owner = pkt.get("assigned_to")
        if current_owner and current_owner != agent:
            return False, f"Packet {packet_id} owned by {current_owner}, not {agent}"
        if self._active_handover(pkt):
            return False, f"Packet {packet_id} already has an active handover"

        files = [item.strip() for item in (files_modified or []) if (item or "").strip()]
        remaining = [item.strip() for item in (remaining_work or []) if (item or "").strip()]
        pkt.setdefault("handovers", [])
        handover_id = f"h-{len(pkt['handovers']) + 1:04d}"
        handover_record = {
            "handover_id": handover_id,
            "from_agent": agent,
            "to_agent": (to_agent or "").strip() or None,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "progress_notes": progress_notes or "",
            "files_modified": files,
            "remaining_work": remaining,
            "active": True,
            "resumed_by": None,
            "resumed_at": None,
        }
        pkt["handovers"].append(handover_record)
        pkt["assigned_to"] = None
        if progress_notes:
            pkt["notes"] = progress_notes
        summary = reason
        if to_agent:
            summary += f" | to: {to_agent}"
        self._log(state, packet_id, "handover", agent, summary)
        self._save(state)
        return True, f"{packet_id} handed over"

    def resume(self, packet_id: str, agent: str) -> Tuple[bool, str]:
        allowed, sup_reason = self._approve("resume", packet_id, agent=agent)
        if not allowed:
            return False, sup_reason

        state = self._load()
        if packet_id not in state.get("packets", {}):
            return False, f"Packet {packet_id} not found"
        pkt = state["packets"][packet_id]
        current_status = normalize_runtime_status(pkt.get("status"))
        if current_status != "in_progress":
            return False, f"Packet {packet_id} is {current_status}, not in_progress"

        active_handover = self._active_handover(pkt)
        if not active_handover:
            return False, f"Packet {packet_id} has no active handover"
        target = active_handover.get("to_agent")
        if target and target != agent:
            return False, f"Packet {packet_id} handover is targeted to {target}"

        active_handover["active"] = False
        active_handover["resumed_by"] = agent
        active_handover["resumed_at"] = datetime.now().isoformat()
        pkt["assigned_to"] = agent
        if not pkt.get("started_at"):
            pkt["started_at"] = datetime.now().isoformat()

        self._log(
            state,
            packet_id,
            "resumed",
            agent,
            f"Resumed handover from {active_handover.get('from_agent') or '-'}",
        )
        self._save(state)
        return True, f"{packet_id} resumed by {agent}"

    def context_bundle(
        self,
        packet_id: str,
        compact: bool = False,
        max_events: int = 40,
        max_notes_bytes: int = 4000,
        max_handovers: int = 40,
    ) -> Tuple[bool, Dict[str, Any]]:
        state = self._load()
        packet_definition = self._find_packet_definition(packet_id)
        if not packet_definition:
            return False, {"message": f"Packet {packet_id} not found"}
        packet_state = state.get("packets", {}).get(packet_id, {})

        max_events = max(1, min(int(max_events), 200))
        max_handovers = max(1, min(int(max_handovers), 200))
        max_notes_bytes = max(200, min(int(max_notes_bytes), 32000))

        status = normalize_runtime_status(packet_state.get("status", "pending"))
        runtime_state = {
            "status": status,
            "assigned_to": packet_state.get("assigned_to"),
            "started_at": packet_state.get("started_at"),
            "completed_at": packet_state.get("completed_at"),
            "notes": packet_state.get("notes"),
        }

        deps = self.definition.get("dependencies", {})
        upstream = []
        for dep_id in deps.get(packet_id, []):
            dep_status = normalize_runtime_status(state.get("packets", {}).get(dep_id, {}).get("status", "pending"))
            upstream.append({"packet_id": dep_id, "status": dep_status})
        downstream = []
        for target, sources in deps.items():
            if packet_id in sources:
                target_status = normalize_runtime_status(state.get("packets", {}).get(target, {}).get("status", "pending"))
                downstream.append({"packet_id": target, "status": target_status})

        full_history = [entry for entry in state.get("log", []) if entry.get("packet_id") == packet_id]
        history = list(reversed(full_history))
        history_dropped = max(0, len(history) - max_events)
        history = history[:max_events]

        handovers_all = [h for h in packet_state.get("handovers", []) if isinstance(h, dict)]
        handovers_dropped = max(0, len(handovers_all) - max_handovers)
        handovers = handovers_all[-max_handovers:]

        notes_bytes_dropped = 0
        runtime_state["notes"], dropped = self._truncate_text(runtime_state.get("notes"), max_notes_bytes)
        notes_bytes_dropped += dropped
        for event in history:
            event["notes"], dropped = self._truncate_text(event.get("notes"), max_notes_bytes)
            notes_bytes_dropped += dropped
        for handover in handovers:
            handover["reason"], dropped = self._truncate_text(handover.get("reason"), max_notes_bytes)
            notes_bytes_dropped += dropped
            handover["progress_notes"], dropped = self._truncate_text(
                handover.get("progress_notes"), max_notes_bytes
            )
            notes_bytes_dropped += dropped

        text_values: List[str] = []
        self._collect_text_values(packet_definition, text_values)
        self._collect_text_values(runtime_state, text_values)
        self._collect_text_values(history, text_values)
        self._collect_text_values(handovers, text_values)
        file_manifest = self._extract_file_manifest(*text_values)

        truncated = history_dropped > 0 or handovers_dropped > 0 or notes_bytes_dropped > 0
        payload = {
            "schema_id": "wbs.context_bundle",
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "mode": "compact" if compact else "full",
            "truncated": truncated,
            "limits": {
                "max_events": max_events,
                "max_notes_bytes": max_notes_bytes,
                "max_handovers": max_handovers,
            },
            "packet_id": packet_id,
            "packet_definition": packet_definition,
            "runtime_state": runtime_state,
            "dependencies": {"upstream": upstream, "downstream": downstream},
            "history": history,
            "handovers": handovers,
            "file_manifest": file_manifest,
            "truncation": {
                "history_dropped": history_dropped,
                "handovers_dropped": handovers_dropped,
                "notes_bytes_dropped": notes_bytes_dropped,
            },
        }
        return True, payload

    def ready(self) -> Dict[str, Any]:
        state = self._load()
        ready: List[Dict[str, str]] = []
        for pkt in self.definition.get("packets", []):
            pid = pkt["id"]
            if normalize_runtime_status(state.get("packets", {}).get(pid, {}).get("status")) == "pending":
                ok, _ = self._deps_met(state, pid)
                if ok:
                    ready.append({"id": pid, "wbs_ref": pkt.get("wbs_ref"), "title": pkt.get("title")})
        return {"ready": ready}

    def briefing(self, recent_events: int = 10, compact: bool = False) -> Dict[str, Any]:
        """Return a versioned session bootstrap summary for operators and agents."""
        state = self._load()
        packets = self.definition.get("packets", [])
        deps = self.definition.get("dependencies", {})
        metadata = self.definition.get("metadata", {})

        counts: Dict[str, int] = {}
        active_assignments: List[Dict[str, Any]] = []
        for pkt in packets:
            pid = pkt["id"]
            pstate = state.get("packets", {}).get(pid, {})
            status = normalize_runtime_status(pstate.get("status", "pending"))
            counts[status] = counts.get(status, 0) + 1
            if status == "in_progress":
                active_assignments.append(
                    {
                        "packet_id": pid,
                        "agent": pstate.get("assigned_to"),
                        "started_at": pstate.get("started_at"),
                    }
                )

        ready_packets = self.ready().get("ready", [])
        blocked_packets: List[Dict[str, Any]] = []
        for pkt in packets:
            pid = pkt["id"]
            pstate = state.get("packets", {}).get(pid, {})
            status = normalize_runtime_status(pstate.get("status", "pending"))
            blockers = []
            for dep_id in deps.get(pid, []):
                dep_state = state.get("packets", {}).get(dep_id, {})
                dep_status = normalize_runtime_status(dep_state.get("status", "pending"))
                if dep_status != "done":
                    blockers.append({"packet_id": dep_id, "status": dep_status})
            if blockers and status in ("pending", "blocked"):
                blocked_packets.append(
                    {
                        "id": pid,
                        "wbs_ref": pkt.get("wbs_ref"),
                        "title": pkt.get("title"),
                        "status": status,
                        "blockers": blockers,
                    }
                )

        all_events = list(reversed(state.get("log", [])))
        recent_events = max(1, min(int(recent_events), 200))
        recent = all_events[:recent_events]
        truncated = len(all_events) > recent_events

        mode = "compact" if compact else "full"
        limits: Dict[str, int] = {"recent_events": recent_events}
        if compact:
            ready_limit = 10
            blocked_limit = 10
            active_limit = 10
            if len(ready_packets) > ready_limit:
                ready_packets = ready_packets[:ready_limit]
                truncated = True
            if len(blocked_packets) > blocked_limit:
                blocked_packets = blocked_packets[:blocked_limit]
                truncated = True
            if len(active_assignments) > active_limit:
                active_assignments = active_assignments[:active_limit]
                truncated = True
            limits.update(
                {
                    "ready_packets": ready_limit,
                    "blocked_packets": blocked_limit,
                    "active_assignments": active_limit,
                }
            )

        return {
            "schema_id": "wbs.briefing",
            "schema_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "mode": mode,
            "truncated": truncated,
            "limits": limits,
            "project": {
                "project_name": metadata.get("project_name"),
                "approved_by": metadata.get("approved_by"),
                "approved_at": metadata.get("approved_at"),
            },
            "counts": counts,
            "ready_packets": ready_packets,
            "blocked_packets": blocked_packets,
            "active_assignments": active_assignments,
            "recent_events": recent,
        }

    def status(self) -> Dict[str, Any]:
        state = self._load()
        return state

    def verify_log(self) -> Tuple[bool, List[str]]:
        state = self._load()
        return verify_log_integrity(state.get("log", []))

    def closeout_l2(self, area_id: str, agent: str, assessment_path: str, notes: str = "") -> Tuple[bool, str]:
        allowed, reason = self._approve("closeout_l2", f"AREA-{area_id}", agent=agent, notes=notes)
        if not allowed:
            return False, reason
        state = self._load()
        area_id = (area_id or "").strip()
        area_ids = {a["id"] for a in self.definition.get("work_areas", [])}
        if area_id not in area_ids and area_id.isdigit():
            area_id = f"{area_id}.0"
        area = next((a for a in self.definition.get("work_areas", []) if a["id"] == area_id), None)
        if not area:
            return False, f"Level-2 area not found: {area_id}"

        area_packets = [p for p in self.definition.get("packets", []) if p.get("area_id") == area_id]
        incomplete = []
        for packet in area_packets:
            pid = packet["id"]
            status = normalize_runtime_status(state.get("packets", {}).get(pid, {}).get("status", "pending"))
            if status != "done":
                incomplete.append(f"{pid}({status})")
        if incomplete:
            return False, f"Cannot close out {area_id}: incomplete packets: {', '.join(incomplete)}"

        raw = Path(assessment_path.strip())
        if not raw.exists():
            return False, f"assessment file not found: {assessment_path}"
        text = raw.read_text(errors="replace").lower()
        missing = [s for s in self.REQUIRED_DRIFT_SECTIONS if s.lower() not in text]
        if missing:
            return False, "Drift assessment validation failed: " + "; ".join(f"missing required section: {m}" for m in missing)

        state.setdefault("area_closeouts", {})[area_id] = {
            "status": "closed",
            "area_title": area.get("title"),
            "closed_by": agent,
            "closed_at": datetime.now().isoformat(),
            "drift_assessment_path": assessment_path,
            "notes": notes or None,
            "integrity_method": "review-based (no cryptographic hashing required)",
        }
        self._log(state, f"AREA-{area_id}", "area_closed", agent, f"Drift assessment: {assessment_path}" + (f" | {notes}" if notes else ""))
        self._save(state)
        return True, f"Level-2 area {area_id} closed"
    REQUIRED_DRIFT_SECTIONS = [
        "## Scope Reviewed",
        "## Expected vs Delivered",
        "## Drift Assessment",
        "## Evidence Reviewed",
        "## Residual Risks",
        "## Immediate Next Actions",
    ]
