import json
from pathlib import Path

from governed_platform.skills.permissions import ExecutionPermissionModel


def load_permission_model(path: Path) -> ExecutionPermissionModel:
    data = json.loads(path.read_text())
    allowed_roots = [Path(p).resolve() for p in data.get("allowed_roots", [])]
    allowed_commands = list(data.get("allowed_commands", []))
    return ExecutionPermissionModel(allowed_roots=allowed_roots, allowed_commands=allowed_commands)
