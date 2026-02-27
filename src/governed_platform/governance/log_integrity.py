import hashlib
import json
from typing import Any, Dict, List, Tuple


LOG_MODE_PLAIN = "plain"
LOG_MODE_HASH_CHAIN = "hash_chain"

_MODE_ALIASES = {
    "plain": LOG_MODE_PLAIN,
    "off": LOG_MODE_PLAIN,
    "disabled": LOG_MODE_PLAIN,
    "none": LOG_MODE_PLAIN,
    "hash": LOG_MODE_HASH_CHAIN,
    "hash_chain": LOG_MODE_HASH_CHAIN,
    "hash-chain": LOG_MODE_HASH_CHAIN,
    "tamper_evident": LOG_MODE_HASH_CHAIN,
    "tamper-evident": LOG_MODE_HASH_CHAIN,
}


def normalize_log_mode(value: Any, strict: bool = False) -> str:
    token = str(value or "").strip().lower().replace(" ", "_")
    if token in _MODE_ALIASES:
        return _MODE_ALIASES[token]
    if strict:
        raise ValueError(f"Invalid log integrity mode: {value!r}")
    return LOG_MODE_PLAIN


def _hash_payload(entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "packet_id": entry.get("packet_id"),
        "event": entry.get("event"),
        "agent": entry.get("agent"),
        "timestamp": entry.get("timestamp"),
        "notes": entry.get("notes"),
        "event_id": entry.get("event_id"),
        "prev_hash": entry.get("prev_hash"),
    }


def compute_entry_hash(entry: Dict[str, Any]) -> str:
    payload = _hash_payload(entry)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


def build_log_entry(
    packet_id: str,
    event: str,
    agent: str,
    notes: str,
    timestamp: str,
    mode: str = LOG_MODE_PLAIN,
    previous_hash: str = "",
    hash_index: int = 1,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "packet_id": packet_id,
        "event": event,
        "agent": agent,
        "timestamp": timestamp,
        "notes": notes,
    }

    normalized = normalize_log_mode(mode)
    if normalized == LOG_MODE_HASH_CHAIN:
        entry["event_id"] = f"evt-{int(hash_index):08d}"
        entry["prev_hash"] = previous_hash or ""
        entry["hash"] = compute_entry_hash(entry)
    return entry


def verify_log_integrity(entries: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    issues = []
    last_hash = ""
    hashed_count = 0

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            issues.append(f"log[{idx}] entry must be an object")
            continue

        has_any_hash_fields = any(field in entry for field in ("event_id", "prev_hash", "hash"))
        has_all_hash_fields = all(field in entry for field in ("event_id", "prev_hash", "hash"))
        if has_any_hash_fields and not has_all_hash_fields:
            issues.append(f"log[{idx}] has partial hash-chain fields (requires event_id, prev_hash, hash)")
            continue
        if not has_all_hash_fields:
            continue

        hashed_count += 1
        expected_event_id = f"evt-{hashed_count:08d}"
        if entry.get("event_id") != expected_event_id:
            issues.append(f"log[{idx}] event_id mismatch (expected {expected_event_id}, got {entry.get('event_id')})")

        expected_prev = last_hash or ""
        if entry.get("prev_hash", "") != expected_prev:
            issues.append(f"log[{idx}] prev_hash mismatch")

        expected_hash = compute_entry_hash(entry)
        if entry.get("hash") != expected_hash:
            issues.append(f"log[{idx}] hash mismatch")

        last_hash = entry.get("hash") or last_hash

    return len(issues) == 0, issues
