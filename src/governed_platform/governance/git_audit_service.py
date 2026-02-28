from pathlib import Path
from typing import Dict, Any, Tuple

from governed_platform.governance.git_ledger import run_governance_auto_commit


def write_git_audit_commit(
    *,
    repo_root: Path,
    packet_id: str,
    action: str,
    actor: str,
    stage_files: list,
    protocol_version: str,
) -> Tuple[bool, Dict[str, Any]]:
    ok, msg, commit_hash, event_id = run_governance_auto_commit(
        repo_root=repo_root,
        packet_id=packet_id,
        action=action,
        actor=actor,
        stage_files=stage_files,
        protocol_version=protocol_version,
    )
    return ok, {
        "message": msg,
        "commit_hash": commit_hash,
        "event_id": event_id,
    }

