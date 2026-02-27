import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from governed_platform.skills.permissions import ExecutionPermissionModel


@dataclass
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str


class SandboxInterface:
    def run(
        self,
        command: List[str],
        workdir: Path,
        permission_model: ExecutionPermissionModel,
        timeout_s: Optional[int] = 60,
    ) -> Tuple[bool, SandboxResult]:
        raise NotImplementedError


class SubprocessSandbox(SandboxInterface):
    """Minimum isolation mode using constrained subprocess execution."""

    def run(
        self,
        command: List[str],
        workdir: Path,
        permission_model: ExecutionPermissionModel,
        timeout_s: Optional[int] = 60,
    ) -> Tuple[bool, SandboxResult]:
        if not command:
            return False, SandboxResult(1, "", "Empty command")

        exe = command[0]
        if not permission_model.is_command_allowed(exe):
            return False, SandboxResult(1, "", f"Command not allowed: {exe}")
        if not permission_model.is_path_allowed(workdir):
            return False, SandboxResult(1, "", f"Workdir not allowed: {workdir}")

        proc = subprocess.run(
            command,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return (proc.returncode == 0), SandboxResult(proc.returncode, proc.stdout, proc.stderr)


class ContainerSandbox(SandboxInterface):
    """Container sandbox contract placeholder for future hardened runtime."""

    def run(
        self,
        command: List[str],
        workdir: Path,
        permission_model: ExecutionPermissionModel,
        timeout_s: Optional[int] = 60,
    ) -> Tuple[bool, SandboxResult]:
        return False, SandboxResult(1, "", "Container sandbox not implemented in this baseline")
