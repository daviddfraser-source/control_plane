from typing import Any, Dict

# Canonical runtime status values stored in state.
RUNTIME_STATUS_VALUES = {
    "pending",
    "preflight",
    "in_progress",
    "stalled",
    "review",
    "escalated",
    "done",
    "failed",
    "blocked",
}

# Packet-definition/schema status values.
PACKET_STATUS_VALUES = {
    "DRAFT",
    "PENDING",
    "PREFLIGHT",
    "IN_PROGRESS",
    "STALLED",
    "REVIEW",
    "ESCALATED",
    "BLOCKED",
    "DONE",
    "FAILED",
}

_RUNTIME_ALIASES = {
    "pending": "pending",
    "draft": "pending",
    "preflight": "preflight",
    "in_progress": "in_progress",
    "inprogress": "in_progress",
    "stalled": "stalled",
    "review": "review",
    "escalated": "escalated",
    "done": "done",
    "complete": "done",
    "completed": "done",
    "failed": "failed",
    "fail": "failed",
    "blocked": "blocked",
}

_PACKET_TO_RUNTIME = {
    "PENDING": "pending",
    "PREFLIGHT": "preflight",
    "IN_PROGRESS": "in_progress",
    "STALLED": "stalled",
    "REVIEW": "review",
    "ESCALATED": "escalated",
    "DONE": "done",
    "FAILED": "failed",
    "BLOCKED": "blocked",
    "DRAFT": "pending",
}

_RUNTIME_TO_PACKET = {
    "pending": "PENDING",
    "preflight": "PREFLIGHT",
    "in_progress": "IN_PROGRESS",
    "stalled": "STALLED",
    "review": "REVIEW",
    "escalated": "ESCALATED",
    "done": "DONE",
    "failed": "FAILED",
    "blocked": "BLOCKED",
}


def _normalize_token(value: Any) -> str:
    token = str(value or "").strip().lower()
    token = token.replace("-", "_").replace(" ", "_")
    return token


def normalize_runtime_status(value: Any, default: str = "pending", strict: bool = False) -> str:
    """Normalize schema/API/legacy status strings to canonical runtime representation."""
    token = _normalize_token(value)
    if token in _RUNTIME_ALIASES:
        return _RUNTIME_ALIASES[token]

    packet_token = token.upper()
    if packet_token in _PACKET_TO_RUNTIME:
        return _PACKET_TO_RUNTIME[packet_token]

    if strict:
        raise ValueError(f"Invalid runtime status: {value!r}")
    return default


def normalize_packet_status(value: Any, default: str = "PENDING", strict: bool = False) -> str:
    """Normalize runtime/API values to packet-definition/schema representation."""
    token = _normalize_token(value)
    if token in _RUNTIME_TO_PACKET:
        return _RUNTIME_TO_PACKET[token]

    packet_token = token.upper()
    if packet_token in PACKET_STATUS_VALUES:
        return packet_token
    if packet_token in {"COMPLETE", "COMPLETED"}:
        return "DONE"

    if strict:
        raise ValueError(f"Invalid packet-definition status: {value!r}")
    return default


def normalize_packet_status_map(state: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize all packet runtime statuses in-place."""
    for pstate in state.get("packets", {}).values():
        if isinstance(pstate, dict):
            pstate["status"] = normalize_runtime_status(pstate.get("status", "pending"))
    return state
