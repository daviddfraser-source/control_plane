import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint_json(payload: Dict[str, Any]) -> str:
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(stable)


def fingerprint_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fingerprint_execution(command: List[str], returncode: int, stdout: str, stderr: str) -> str:
    payload = {
        "command": command,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
    }
    return fingerprint_json(payload)
