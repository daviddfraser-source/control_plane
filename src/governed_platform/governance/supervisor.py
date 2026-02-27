from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional, Tuple, Protocol, Dict, Any, List

from governed_platform.governance.file_lock import atomic_write_json

ENFORCEMENT_DISABLED = "disabled"
ENFORCEMENT_ADVISORY = "advisory"
ENFORCEMENT_STRICT = "strict"
ENFORCEMENT_MODES = {ENFORCEMENT_DISABLED, ENFORCEMENT_ADVISORY, ENFORCEMENT_STRICT}
DEFAULT_CAPABILITY_TAXONOMY = ["code", "test", "docs", "review", "research", "deploy"]


@dataclass
class TransitionRequest:
    packet_id: str
    action: str
    agent: Optional[str] = None
    notes: Optional[str] = None
    required_capabilities: Optional[List[str]] = None


class SupervisorInterface(Protocol):
    def approve(self, req: TransitionRequest) -> Tuple[bool, str]:
        ...


@dataclass
class SupervisorPolicy:
    require_notes_on_done: bool = True
    require_agent_for_mutation: bool = True
    agent_registry_path: Optional[Path] = None


def _default_registry_path() -> Path:
    return (Path.cwd() / ".governance" / "agents.json").resolve()


def default_agent_registry() -> Dict[str, Any]:
    return {
        "version": "1.0",
        "enforcement_mode": ENFORCEMENT_DISABLED,
        "capability_taxonomy": DEFAULT_CAPABILITY_TAXONOMY.copy(),
        "agents": [],
    }


def normalize_enforcement_mode(mode: Any) -> str:
    token = str(mode or "").strip().lower()
    if token in ENFORCEMENT_MODES:
        return token
    return ENFORCEMENT_ADVISORY


def load_agent_registry(path: Optional[Path] = None) -> Dict[str, Any]:
    target = Path(path or _default_registry_path())
    if not target.exists():
        return default_agent_registry()
    data = json.loads(target.read_text())
    data.setdefault("version", "1.0")
    data.setdefault("enforcement_mode", ENFORCEMENT_ADVISORY)
    data["enforcement_mode"] = normalize_enforcement_mode(data.get("enforcement_mode"))
    data.setdefault("capability_taxonomy", DEFAULT_CAPABILITY_TAXONOMY.copy())
    data.setdefault("agents", [])
    return data


def save_agent_registry(registry: Dict[str, Any], path: Optional[Path] = None) -> None:
    target = Path(path or _default_registry_path())
    registry["enforcement_mode"] = normalize_enforcement_mode(registry.get("enforcement_mode"))
    registry.setdefault("version", "1.0")
    registry.setdefault("capability_taxonomy", DEFAULT_CAPABILITY_TAXONOMY.copy())
    registry.setdefault("agents", [])
    atomic_write_json(target, registry)


def check_agent_capabilities(
    required_capabilities: List[str], agent_id: str, path: Optional[Path] = None
) -> Tuple[bool, str, str]:
    registry = load_agent_registry(path)
    mode = normalize_enforcement_mode(registry.get("enforcement_mode"))
    required = [str(cap).strip() for cap in (required_capabilities or []) if str(cap).strip()]
    if mode == ENFORCEMENT_DISABLED or not required:
        return True, "", mode

    taxonomy = {str(cap).strip() for cap in registry.get("capability_taxonomy", [])}
    unknown_required = [cap for cap in required if cap not in taxonomy]
    profiles = {str(agent.get("id")): agent for agent in registry.get("agents", []) if isinstance(agent, dict)}
    profile = profiles.get(agent_id)
    agent_caps = {str(cap).strip() for cap in (profile or {}).get("capabilities", [])}
    missing = sorted([cap for cap in required if cap not in agent_caps])

    issues = []
    if not profile:
        issues.append(f"agent '{agent_id}' is not registered")
    if missing:
        issues.append(f"missing required capabilities: {', '.join(missing)}")
    if unknown_required:
        issues.append(f"unknown required capability tags: {', '.join(sorted(set(unknown_required)))}")

    if not issues:
        return True, "", mode

    message = "Capability check: " + "; ".join(issues)
    if mode == ENFORCEMENT_STRICT:
        return False, message, mode
    return True, f"Capability warning: {'; '.join(issues)}", mode


class DeterministicSupervisor:
    """Default deterministic authority policy for packet transitions."""

    def __init__(self, policy: SupervisorPolicy = None):
        self.policy = policy or SupervisorPolicy()

    def approve(self, req: TransitionRequest) -> Tuple[bool, str]:
        if self.policy.require_agent_for_mutation and req.action in {
            "claim",
            "done",
            "note",
            "fail",
            "handover",
            "resume",
            "closeout_l2",
        }:
            if not req.agent:
                return False, "Supervisor denied: agent required"
        if self.policy.require_notes_on_done and req.action == "done" and not (req.notes or "").strip():
            return False, "Supervisor denied: completion notes required for done"
        if req.action == "claim":
            ok, message, _ = check_agent_capabilities(
                req.required_capabilities or [],
                req.agent or "",
                path=self.policy.agent_registry_path,
            )
            if not ok:
                return False, message
            if message:
                return True, message
        return True, "approved"
