import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
import zipfile

from governed_platform.governance.canonical_json import canonical_json_dumps
from governed_platform.governance.file_lock import file_lock


GENESIS = "GENESIS"
HASH_ALGORITHM = "sha256"
CANONICALIZATION_VERSION = "1.0"
DCL_SCHEMA_VERSION = "1.0"

DCL_DEFAULT_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "heartbeat_commit_policy": "transition_only",
    "mode": "dcl",
    "dcl_version": DCL_SCHEMA_VERSION,
    "canonicalization_version": CANONICALIZATION_VERSION,
    "hash_algorithm": HASH_ALGORITHM,
    "state_schema_version": "1.1",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_hex(value: Any) -> str:
    payload = canonical_json_dumps(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_diff(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    diff: Dict[str, Any] = {"changed": {}, "added": {}, "removed": {}}
    before = before or {}
    after = after or {}

    for key in sorted(before.keys() | after.keys()):
        if key not in before:
            diff["added"][key] = after[key]
        elif key not in after:
            diff["removed"][key] = before[key]
        elif before[key] != after[key]:
            diff["changed"][key] = {"from": before[key], "to": after[key]}
    return diff


def dcl_root(repo_root: Path) -> Path:
    return repo_root / ".governance" / "dcl"


def packet_root(repo_root: Path, packet_id: str) -> Path:
    return dcl_root(repo_root) / "packets" / packet_id


def commits_root(repo_root: Path, packet_id: str) -> Path:
    return packet_root(repo_root, packet_id) / "commits"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _load_head(repo_root: Path, packet_id: str) -> Dict[str, Any]:
    return _read_json(packet_root(repo_root, packet_id) / "HEAD", {"seq": 0, "commit_hash": GENESIS})


def _save_head(repo_root: Path, packet_id: str, seq: int, commit_hash: str) -> None:
    _write_json(packet_root(repo_root, packet_id) / "HEAD", {"seq": seq, "commit_hash": commit_hash})


def _constitution_hash(repo_root: Path) -> str:
    path = repo_root / "constitution.md"
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _action_envelope(action: str, actor: str, inputs: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    return {
        "type": "transition",
        "name": action,
        "actor": {"kind": "agent", "id": actor or "system"},
        "reason": reason or "",
        "inputs": inputs or {},
        "timestamp": now_utc(),
    }


def write_commit(
    *,
    repo_root: Path,
    packet_id: str,
    action: str,
    actor: str,
    pre_state: Dict[str, Any],
    post_state: Dict[str, Any],
    reason: str = "",
    inputs: Dict[str, Any] = None,
) -> Dict[str, Any]:
    lock_target = packet_root(repo_root, packet_id) / "HEAD"
    with file_lock(lock_target, timeout=30.0):
        head = _load_head(repo_root, packet_id)
        prev_hash = head.get("commit_hash", GENESIS)
        seq = int(head.get("seq", 0)) + 1

        action_env = _action_envelope(action, actor, inputs or {}, reason=reason)
        action_hash = sha256_hex(action_env)
        pre_hash = sha256_hex(pre_state or {})
        post_hash = sha256_hex(post_state or {})
        diff = build_diff(pre_state or {}, post_state or {})
        base = {
            "commit_id": f"CMT-{packet_id}-{seq:06d}",
            "packet_id": packet_id,
            "seq": seq,
            "prev_commit_hash": prev_hash if seq > 1 else GENESIS,
            "action_hash": action_hash,
            "pre_state_hash": pre_hash,
            "post_state_hash": post_hash,
            "constitution_hash": _constitution_hash(repo_root),
            "diff": diff,
            "created_at": now_utc(),
            "action_envelope": action_env,
        }
        commit_hash = sha256_hex(base)
        commit = deepcopy(base)
        commit["commit_hash"] = commit_hash

        # Transaction journal (file-mode atomicity aid)
        root = packet_root(repo_root, packet_id)
        journal = root / "journal.json"
        _write_json(journal, {"stage": "prepare", "seq": seq, "commit_hash": commit_hash})

        target = commits_root(repo_root, packet_id) / f"{seq:06d}.json"
        _write_json(target, commit)
        _save_head(repo_root, packet_id, seq, commit_hash)

        _write_json(journal, {"stage": "done", "seq": seq, "commit_hash": commit_hash})
        journal.unlink(missing_ok=True)
        return commit


def _list_commits(repo_root: Path, packet_id: str) -> List[Dict[str, Any]]:
    root = commits_root(repo_root, packet_id)
    if not root.exists():
        return []
    rows = []
    for path in sorted(root.glob("*.json")):
        rows.append(json.loads(path.read_text()))
    return rows


def verify_packet(repo_root: Path, packet_id: str) -> Tuple[bool, List[str]]:
    detail = verify_packet_detailed(repo_root, packet_id)
    return len(detail.get("issues", [])) == 0, list(detail.get("issues", []))


def verify_packet_detailed(
    repo_root: Path,
    packet_id: str,
    state_packet: Dict[str, Any] = None,
) -> Dict[str, Any]:
    commits = _list_commits(repo_root, packet_id)
    head = _load_head(repo_root, packet_id)
    detail: Dict[str, Any] = {
        "packet_id": packet_id,
        "commit_count": len(commits),
        "checked_commits": 0,
        "issues": [],
        "head": {"seq": int(head.get("seq", 0)), "commit_hash": str(head.get("commit_hash", GENESIS))},
    }
    if not commits:
        if state_packet:
            detail["issues"].append(f"missing DCL commits for packet with runtime state: {packet_id}")
        return detail
    prev_commit = None
    seen_seq = set()
    for idx, commit in enumerate(commits):
        detail["checked_commits"] += 1
        seq = idx + 1
        commit_seq = int(commit.get("seq", 0))
        if commit_seq in seen_seq:
            detail["issues"].append(f"duplicate seq value at {packet_id}: {commit_seq}")
        seen_seq.add(commit_seq)
        if commit_seq != seq:
            detail["issues"].append(f"seq mismatch at {packet_id}#{idx}: expected {seq}")
        envelope = commit.get("action_envelope", {})
        if sha256_hex(envelope) != commit.get("action_hash"):
            detail["issues"].append(f"action_hash mismatch at {packet_id}#{seq}")
        # Recompute hash of commit without self-hash field.
        base = deepcopy(commit)
        base.pop("commit_hash", None)
        if sha256_hex(base) != commit.get("commit_hash"):
            detail["issues"].append(f"commit_hash mismatch at {packet_id}#{seq}")
        if prev_commit is None:
            if commit.get("prev_commit_hash") != GENESIS:
                detail["issues"].append(f"genesis prev_commit_hash mismatch at {packet_id}#{seq}")
        else:
            if commit.get("prev_commit_hash") != prev_commit.get("commit_hash"):
                detail["issues"].append(f"prev_commit_hash mismatch at {packet_id}#{seq}")
            if commit.get("pre_state_hash") != prev_commit.get("post_state_hash"):
                detail["issues"].append(f"pre/post state chain mismatch at {packet_id}#{seq}")
        prev_commit = commit

    last = commits[-1]
    if int(head.get("seq", 0)) != int(last.get("seq", 0)):
        detail["issues"].append(
            f"HEAD seq mismatch at {packet_id}: head={head.get('seq')} last={last.get('seq')}"
        )
    if str(head.get("commit_hash", "")) != str(last.get("commit_hash", "")):
        detail["issues"].append(
            f"HEAD hash mismatch at {packet_id}: head={head.get('commit_hash')} last={last.get('commit_hash')}"
        )

    if state_packet:
        current_hash = sha256_hex(state_packet)
        if str(last.get("post_state_hash", "")) != current_hash:
            detail["issues"].append(
                f"runtime state mismatch at {packet_id}: state_hash != HEAD.post_state_hash"
            )
    return detail


def verify_all(repo_root: Path) -> Tuple[bool, Dict[str, List[str]]]:
    ok, details = verify_all_detailed(repo_root)
    issues = {
        packet_id: list(payload.get("issues", []))
        for packet_id, payload in details.items()
        if payload.get("issues")
    }
    return ok, issues


def verify_all_detailed(
    repo_root: Path,
    state_packets: Dict[str, Dict[str, Any]] = None,
) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    packets_dir = dcl_root(repo_root) / "packets"
    if not packets_dir.exists():
        return True, {}
    details: Dict[str, Dict[str, Any]] = {}
    for packet_dir in sorted(packets_dir.iterdir()):
        if not packet_dir.is_dir():
            continue
        packet_id = packet_dir.name
        details[packet_id] = verify_packet_detailed(
            repo_root,
            packet_id,
            (state_packets or {}).get(packet_id),
        )

    ok = all(not payload.get("issues") for payload in details.values())
    return ok, details


def validate_config_lock(config: Dict[str, Any], expected_state_schema: str = "") -> List[str]:
    merged = dict(DCL_DEFAULT_CONFIG)
    merged.update(config or {})
    issues: List[str] = []
    if str(merged.get("mode", "")).strip().lower() != "dcl":
        issues.append(f"dcl-config mode must be 'dcl' (found: {merged.get('mode')})")
    if str(merged.get("hash_algorithm", "")).strip().lower() != HASH_ALGORITHM:
        issues.append(
            f"dcl-config hash_algorithm mismatch (expected {HASH_ALGORITHM}, found {merged.get('hash_algorithm')})"
        )
    if str(merged.get("canonicalization_version", "")).strip() != CANONICALIZATION_VERSION:
        issues.append(
            f"dcl-config canonicalization_version mismatch (expected {CANONICALIZATION_VERSION}, found {merged.get('canonicalization_version')})"
        )
    if str(merged.get("dcl_version", "")).strip() != DCL_SCHEMA_VERSION:
        issues.append(
            f"dcl-config dcl_version mismatch (expected {DCL_SCHEMA_VERSION}, found {merged.get('dcl_version')})"
        )
    if expected_state_schema:
        actual = str(merged.get("state_schema_version", "")).strip()
        if actual and actual != str(expected_state_schema).strip():
            issues.append(
                f"dcl-config state_schema_version mismatch (expected {expected_state_schema}, found {actual})"
            )
    return issues


def recover_packet_journal(repo_root: Path, packet_id: str) -> Dict[str, Any]:
    root = packet_root(repo_root, packet_id)
    journal = root / "journal.json"
    if not journal.exists():
        return {"packet_id": packet_id, "recovered": False, "status": "none"}
    payload = _read_json(journal, {})
    seq = int(payload.get("seq", 0) or 0)
    commit_hash = str(payload.get("commit_hash", "") or "")
    commit_file = commits_root(repo_root, packet_id) / f"{seq:06d}.json"
    if seq > 0 and commit_hash and commit_file.exists():
        _save_head(repo_root, packet_id, seq, commit_hash)
        journal.unlink(missing_ok=True)
        return {
            "packet_id": packet_id,
            "recovered": True,
            "status": "recovered",
            "seq": seq,
            "commit_hash": commit_hash,
        }
    return {
        "packet_id": packet_id,
        "recovered": False,
        "status": "blocked",
        "issue": "journal present but commit payload incomplete",
        "seq": seq,
        "commit_hash": commit_hash,
    }


def recover_all_journals(repo_root: Path) -> List[Dict[str, Any]]:
    packets_dir = dcl_root(repo_root) / "packets"
    if not packets_dir.exists():
        return []
    reports: List[Dict[str, Any]] = []
    for packet_dir in sorted(packets_dir.iterdir()):
        if not packet_dir.is_dir():
            continue
        reports.append(recover_packet_journal(repo_root, packet_dir.name))
    return reports


def history(repo_root: Path, packet_id: str) -> List[Dict[str, Any]]:
    return _list_commits(repo_root, packet_id)


def export_proof_bundle(repo_root: Path, packet_id: str, out_path: Path) -> Path:
    out_path = out_path.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    commits = commits_root(repo_root, packet_id)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if commits.exists():
            for path in sorted(commits.glob("*.json")):
                zf.write(path, arcname=f"commits/{path.name}")
        head = packet_root(repo_root, packet_id) / "HEAD"
        if head.exists():
            zf.write(head, arcname="HEAD")
        constitution = repo_root / "constitution.md"
        if constitution.exists():
            zf.write(constitution, arcname="constitution.md")
    return out_path


def write_project_checkpoint(repo_root: Path, phase: str, packet_heads: Dict[str, str]) -> Dict[str, Any]:
    root = dcl_root(repo_root) / "project-checkpoints"
    root.mkdir(parents=True, exist_ok=True)
    merkle = sha256_hex(packet_heads)
    seq = len(list(root.glob("*.json"))) + 1
    payload = {
        "checkpoint_id": f"CHK-{seq:06d}",
        "phase": phase,
        "packet_heads": packet_heads,
        "merkle_root": merkle,
        "created_at": now_utc(),
    }
    payload["checkpoint_hash"] = sha256_hex(payload)
    _write_json(root / f"{seq:06d}.json", payload)
    return payload
