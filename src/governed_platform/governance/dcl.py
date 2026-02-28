import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
import zipfile

from governed_platform.governance.canonical_json import canonical_json_dumps


GENESIS = "GENESIS"


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
    commits = _list_commits(repo_root, packet_id)
    if not commits:
        return True, []
    issues: List[str] = []
    prev_commit = None
    for idx, commit in enumerate(commits):
        seq = idx + 1
        if int(commit.get("seq", 0)) != seq:
            issues.append(f"seq mismatch at {packet_id}#{idx}: expected {seq}")
        envelope = commit.get("action_envelope", {})
        if sha256_hex(envelope) != commit.get("action_hash"):
            issues.append(f"action_hash mismatch at {packet_id}#{seq}")
        # Recompute hash of commit without self-hash field.
        base = deepcopy(commit)
        base.pop("commit_hash", None)
        if sha256_hex(base) != commit.get("commit_hash"):
            issues.append(f"commit_hash mismatch at {packet_id}#{seq}")
        if prev_commit is None:
            if commit.get("prev_commit_hash") != GENESIS:
                issues.append(f"genesis prev_commit_hash mismatch at {packet_id}#{seq}")
        else:
            if commit.get("prev_commit_hash") != prev_commit.get("commit_hash"):
                issues.append(f"prev_commit_hash mismatch at {packet_id}#{seq}")
            if commit.get("pre_state_hash") != prev_commit.get("post_state_hash"):
                issues.append(f"pre/post state chain mismatch at {packet_id}#{seq}")
        prev_commit = commit
    return len(issues) == 0, issues


def verify_all(repo_root: Path) -> Tuple[bool, Dict[str, List[str]]]:
    packets_dir = dcl_root(repo_root) / "packets"
    if not packets_dir.exists():
        return True, {}
    issues: Dict[str, List[str]] = {}
    for packet_dir in sorted(packets_dir.iterdir()):
        if not packet_dir.is_dir():
            continue
        packet_id = packet_dir.name
        ok, errs = verify_packet(repo_root, packet_id)
        if not ok:
            issues[packet_id] = errs
    return len(issues) == 0, issues


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

