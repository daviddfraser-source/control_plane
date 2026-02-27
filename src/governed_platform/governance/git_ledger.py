from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple


SUBJECT_PATTERN = re.compile(
    r"^substrate\(packet=(?P<packet>[^,]+),action=(?P<action>[^,]+),actor=(?P<actor>[^)]+)\)$"
)

PROTOCOL_VERSION = "1"
TRAILER_PROTOCOL = "Substrate-Protocol"
TRAILER_EVENT_ID = "Substrate-Event-ID"
TRAILER_PACKET = "Substrate-Packet"
TRAILER_ACTION = "Substrate-Action"
TRAILER_ACTOR = "Substrate-Actor"
TRAILER_TIMESTAMP = "Substrate-Timestamp"
TRAILER_AREA = "Substrate-Area"
TRAILER_CLOSEOUT = "Substrate-Closeout"

REQUIRED_TRAILERS = (
    TRAILER_PROTOCOL,
    TRAILER_EVENT_ID,
    TRAILER_PACKET,
    TRAILER_ACTION,
    TRAILER_ACTOR,
    TRAILER_TIMESTAMP,
)
OPTIONAL_TRAILERS = (
    TRAILER_AREA,
    TRAILER_CLOSEOUT,
)

GIT_MODE_DISABLED = "disabled"
GIT_MODE_ADVISORY = "advisory"
GIT_MODE_STRICT = "strict"
GIT_MODES = {GIT_MODE_DISABLED, GIT_MODE_ADVISORY, GIT_MODE_STRICT}


def _norm(value: Any) -> str:
    return str(value or "").strip()


def normalize_git_mode(mode: Any) -> str:
    token = _norm(mode).lower()
    if token in GIT_MODES:
        return token
    return GIT_MODE_DISABLED


def default_git_governance_config() -> Dict[str, Any]:
    return {
        "version": "1.0",
        "mode": GIT_MODE_DISABLED,
        "auto_commit": False,
        "commit_protocol_version": PROTOCOL_VERSION,
        "stage_files": [".governance/wbs-state.json"],
    }


def load_git_governance_config(path: Path) -> Dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return default_git_governance_config()
    payload = json.loads(target.read_text())
    if not isinstance(payload, dict):
        payload = {}
    out = default_git_governance_config()
    out.update(payload)
    out["mode"] = normalize_git_mode(out.get("mode"))
    out["auto_commit"] = bool(out.get("auto_commit"))
    stage_files = out.get("stage_files")
    if not isinstance(stage_files, list) or not stage_files:
        out["stage_files"] = [".governance/wbs-state.json"]
    else:
        out["stage_files"] = [_norm(item) for item in stage_files if _norm(item)]
    out["commit_protocol_version"] = _norm(out.get("commit_protocol_version")) or PROTOCOL_VERSION
    return out


def save_git_governance_config(path: Path, config: Dict[str, Any]) -> None:
    target = Path(path)
    normalized = default_git_governance_config()
    normalized.update(config or {})
    normalized["mode"] = normalize_git_mode(normalized.get("mode"))
    normalized["auto_commit"] = bool(normalized.get("auto_commit"))
    stage_files = normalized.get("stage_files")
    if not isinstance(stage_files, list) or not stage_files:
        normalized["stage_files"] = [".governance/wbs-state.json"]
    else:
        normalized["stage_files"] = [_norm(item) for item in stage_files if _norm(item)]
    normalized["commit_protocol_version"] = _norm(normalized.get("commit_protocol_version")) or PROTOCOL_VERSION
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(normalized, indent=2) + "\n")


def _validate_iso8601(value: str) -> None:
    token = _norm(value)
    if not token:
        raise ValueError("timestamp is required")
    try:
        if token.endswith("Z"):
            token = token[:-1] + "+00:00"
        datetime.fromisoformat(token)
    except Exception as exc:
        raise ValueError(f"invalid ISO-8601 timestamp: {value!r}") from exc


def build_commit_subject(packet_id: str, action: str, actor: str) -> str:
    packet = _norm(packet_id)
    act = _norm(action)
    who = _norm(actor)
    if not packet or not act or not who:
        raise ValueError("packet_id, action, and actor are required")
    return f"substrate(packet={packet},action={act},actor={who})"


def format_governance_commit(
    packet_id: str,
    action: str,
    actor: str,
    event_id: str,
    timestamp: str,
    protocol_version: str = PROTOCOL_VERSION,
    area_id: str = "",
    closeout_area: str = "",
) -> str:
    packet = _norm(packet_id)
    act = _norm(action)
    who = _norm(actor)
    eid = _norm(event_id)
    pver = _norm(protocol_version) or PROTOCOL_VERSION
    area = _norm(area_id)
    closeout = _norm(closeout_area)
    _validate_iso8601(timestamp)

    if not eid:
        raise ValueError("event_id is required")

    lines = [
        build_commit_subject(packet, act, who),
        "",
        f"{TRAILER_PROTOCOL}: {pver}",
        f"{TRAILER_EVENT_ID}: {eid}",
        f"{TRAILER_PACKET}: {packet}",
        f"{TRAILER_ACTION}: {act}",
        f"{TRAILER_ACTOR}: {who}",
        f"{TRAILER_TIMESTAMP}: {_norm(timestamp)}",
    ]
    if area:
        lines.append(f"{TRAILER_AREA}: {area}")
    if closeout:
        lines.append(f"{TRAILER_CLOSEOUT}: {closeout}")
    return "\n".join(lines)


def parse_governance_commit(message: str) -> Dict[str, str]:
    text = str(message or "")
    lines = text.splitlines()
    subject = ""
    for line in lines:
        token = line.strip()
        if token:
            subject = token
            break
    if not subject:
        raise ValueError("commit message is empty")

    subject_match = SUBJECT_PATTERN.fullmatch(subject)
    if not subject_match:
        raise ValueError("commit subject does not match substrate protocol")

    trailers: Dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key.startswith("Substrate-"):
            if key in trailers:
                raise ValueError(f"duplicate trailer: {key}")
            trailers[key] = value.strip()

    for key in REQUIRED_TRAILERS:
        if not _norm(trailers.get(key)):
            raise ValueError(f"missing required trailer: {key}")

    packet = _norm(subject_match.group("packet"))
    action = _norm(subject_match.group("action"))
    actor = _norm(subject_match.group("actor"))
    if packet != _norm(trailers.get(TRAILER_PACKET)):
        raise ValueError("subject/trailer mismatch for packet")
    if action != _norm(trailers.get(TRAILER_ACTION)):
        raise ValueError("subject/trailer mismatch for action")
    if actor != _norm(trailers.get(TRAILER_ACTOR)):
        raise ValueError("subject/trailer mismatch for actor")

    _validate_iso8601(trailers[TRAILER_TIMESTAMP])

    out = {
        "protocol_version": _norm(trailers[TRAILER_PROTOCOL]),
        "event_id": _norm(trailers[TRAILER_EVENT_ID]),
        "packet_id": packet,
        "action": action,
        "actor": actor,
        "timestamp": _norm(trailers[TRAILER_TIMESTAMP]),
        "subject": subject,
    }
    if _norm(trailers.get(TRAILER_AREA)):
        out["area_id"] = _norm(trailers[TRAILER_AREA])
    if _norm(trailers.get(TRAILER_CLOSEOUT)):
        out["closeout_area"] = _norm(trailers[TRAILER_CLOSEOUT])
    return out


def generate_event_id() -> str:
    now = datetime.now(timezone.utc)
    return f"evt-{now.strftime('%Y%m%d%H%M%S%f')}"


def _run_git(args: List[str], cwd: Path, stdin: str = "") -> Tuple[bool, str]:
    proc = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        input=stdin if stdin else None,
        text=True,
        capture_output=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output.strip()


def ensure_git_worktree(cwd: Path) -> Tuple[bool, str]:
    ok, output = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=Path(cwd))
    if not ok:
        return False, output or "git worktree not detected"
    if output.strip().lower() != "true":
        return False, "not inside a git worktree"
    return True, ""


def run_governance_auto_commit(
    repo_root: Path,
    packet_id: str,
    action: str,
    actor: str,
    stage_files: List[str],
    protocol_version: str = PROTOCOL_VERSION,
    event_id: str = "",
    timestamp: str = "",
    area_id: str = "",
    closeout_area: str = "",
) -> Tuple[bool, str, str, str]:
    root = Path(repo_root)
    ok, reason = ensure_git_worktree(root)
    if not ok:
        return False, reason, "", ""

    files = [_norm(item) for item in (stage_files or []) if _norm(item)]
    if not files:
        return False, "no stage_files configured for governance auto-commit", "", ""

    effective_timestamp = _norm(timestamp) or datetime.now(timezone.utc).isoformat()
    effective_event = _norm(event_id) or generate_event_id()
    commit_message = format_governance_commit(
        packet_id=packet_id,
        action=action,
        actor=actor,
        event_id=effective_event,
        timestamp=effective_timestamp,
        protocol_version=protocol_version,
        area_id=area_id,
        closeout_area=closeout_area,
    )

    ok, output = _run_git(["add", "--"] + files, cwd=root)
    if not ok:
        return False, output or "git add failed", "", effective_event

    ok, output = _run_git(["commit", "-F", "-"], cwd=root, stdin=commit_message)
    if not ok:
        return False, output or "git commit failed", "", effective_event

    ok, output = _run_git(["rev-parse", "HEAD"], cwd=root)
    if not ok:
        return False, output or "failed to resolve HEAD commit", "", effective_event
    commit_hash = output.strip().splitlines()[-1].strip()
    return True, "ok", commit_hash, effective_event


def read_commit_message(repo_root: Path, commit_hash: str) -> Tuple[bool, str]:
    root = Path(repo_root)
    ok, output = _run_git(["show", "-s", "--format=%B", commit_hash], cwd=root)
    if not ok:
        return False, output or f"failed to read commit message for {commit_hash}"
    return True, output


def parse_governance_commit_from_hash(repo_root: Path, commit_hash: str) -> Tuple[bool, Dict[str, str], str]:
    ok, payload = read_commit_message(repo_root, commit_hash)
    if not ok:
        return False, {}, payload
    try:
        parsed = parse_governance_commit(payload)
    except ValueError as e:
        return False, {}, str(e)
    return True, parsed, ""


def _branch_component(value: Any) -> str:
    token = _norm(value).lower()
    token = re.sub(r"[^a-z0-9._-]+", "-", token)
    token = re.sub(r"-{2,}", "-", token).strip("-")
    return token or "unknown"


def build_packet_branch_name(packet_id: str, agent: str) -> str:
    packet = _branch_component(packet_id)
    actor = _branch_component(agent)
    return f"substrate/{packet}/{actor}"


def current_branch(repo_root: Path) -> Tuple[bool, str]:
    ok, output = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=Path(repo_root))
    if not ok:
        return False, output or "unable to resolve current branch"
    return True, output.strip().splitlines()[-1].strip()


def open_packet_branch(repo_root: Path, packet_id: str, agent: str, from_ref: str = "") -> Tuple[bool, str, str]:
    root = Path(repo_root)
    ok, reason = ensure_git_worktree(root)
    if not ok:
        return False, "", reason

    branch = build_packet_branch_name(packet_id, agent)
    args = ["checkout", "-b", branch]
    if _norm(from_ref):
        args.append(_norm(from_ref))
    ok, output = _run_git(args, cwd=root)
    if not ok:
        return False, branch, output or "failed to create packet branch"
    return True, branch, "ok"


def close_packet_branch(
    repo_root: Path,
    packet_id: str,
    agent: str,
    base_branch: str = "main",
    delete_branch: bool = True,
) -> Tuple[bool, str, str]:
    root = Path(repo_root)
    ok, reason = ensure_git_worktree(root)
    if not ok:
        return False, "", reason

    branch = build_packet_branch_name(packet_id, agent)
    base = _norm(base_branch) or "main"

    ok, output = _run_git(["checkout", base], cwd=root)
    if not ok:
        return False, branch, output or f"failed to checkout base branch {base}"

    ok, output = _run_git(["merge", "--ff-only", branch], cwd=root)
    if not ok:
        return False, branch, output or f"failed to merge branch {branch} into {base}"

    if delete_branch:
        ok, output = _run_git(["branch", "-d", branch], cwd=root)
        if not ok:
            return False, branch, output or f"failed to delete branch {branch}"

    return True, branch, "ok"


def build_closeout_tag(area_id: str, timestamp: str = "") -> str:
    area = _branch_component(str(area_id or "").replace(".", "-"))
    if _norm(timestamp):
        token = _norm(timestamp)
        try:
            dt = datetime.fromisoformat(token.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    stamp = dt.strftime("%Y%m%d%H%M%S")
    return f"substrate-closeout-{area}-{stamp}"


def create_tag(repo_root: Path, tag_name: str, commit_hash: str) -> Tuple[bool, str]:
    root = Path(repo_root)
    ok, reason = ensure_git_worktree(root)
    if not ok:
        return False, reason
    tag = _norm(tag_name)
    commit = _norm(commit_hash)
    if not tag or not commit:
        return False, "tag name and commit hash are required"
    ok, output = _run_git(["tag", tag, commit], cwd=root)
    if not ok:
        return False, output or f"failed to create tag {tag}"
    return True, "ok"


def reconstruct_governance_history(repo_root: Path, limit: int = 500) -> Tuple[bool, List[Dict[str, str]], str]:
    root = Path(repo_root)
    ok, reason = ensure_git_worktree(root)
    if not ok:
        return False, [], reason

    count = max(1, int(limit))
    format_spec = "%H%x1f%B%x1e"
    ok, output = _run_git(["log", "-n", str(count), f"--format={format_spec}"], cwd=root)
    if not ok:
        return False, [], output or "failed to read git log"

    entries = []
    chunks = output.split("\x1e")
    for chunk in chunks:
        payload = chunk.strip()
        if not payload:
            continue
        if "\x1f" not in payload:
            continue
        commit_hash, message = payload.split("\x1f", 1)
        try:
            parsed = parse_governance_commit(message.strip())
        except ValueError:
            continue
        parsed["commit"] = commit_hash.strip()
        entries.append(parsed)
    return True, entries, ""
