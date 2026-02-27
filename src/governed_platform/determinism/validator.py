import json
from pathlib import Path
from typing import Dict, Any, List

from governed_platform.determinism.fingerprint import (
    fingerprint_json,
    fingerprint_file,
    fingerprint_execution,
)


def build_reproducibility_record(
    execution: Dict[str, Any],
    state_payload: Dict[str, Any],
    artifact_paths: List[Path],
) -> Dict[str, Any]:
    artifacts = {}
    for path in artifact_paths:
        if path.exists():
            artifacts[str(path)] = fingerprint_file(path)
        else:
            artifacts[str(path)] = None

    record = {
        "execution_fingerprint": fingerprint_execution(
            execution.get("command", []),
            execution.get("returncode", 0),
            execution.get("stdout", ""),
            execution.get("stderr", ""),
        ),
        "state_fingerprint": fingerprint_json(state_payload),
        "artifact_fingerprints": artifacts,
    }
    return record


def compare_records(lhs: Dict[str, Any], rhs: Dict[str, Any]) -> bool:
    return json.dumps(lhs, sort_keys=True) == json.dumps(rhs, sort_keys=True)
