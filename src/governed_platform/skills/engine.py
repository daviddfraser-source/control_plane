from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

from governed_platform.skills.permissions import ExecutionPermissionModel
from governed_platform.skills.sandbox import SandboxInterface, SubprocessSandbox


@dataclass
class SkillExecutionRequest:
    skill_name: str
    command: List[str]
    workdir: Path
    timeout_s: int = 60


class SkillExecutionEngine:
    """Mediates skill execution through sandbox and permission model."""

    def __init__(self, sandbox: Optional[SandboxInterface] = None):
        self.sandbox = sandbox or SubprocessSandbox()

    def execute(self, req: SkillExecutionRequest, perms: ExecutionPermissionModel) -> Dict[str, Any]:
        ok, result = self.sandbox.run(
            command=req.command,
            workdir=req.workdir,
            permission_model=perms,
            timeout_s=req.timeout_s,
        )
        return {
            "success": ok,
            "skill_name": req.skill_name,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
