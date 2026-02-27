import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class LockTimeoutError(TimeoutError):
    """Raised when lock acquisition exceeds timeout budget."""


def _lock_path_for(path: Path) -> Path:
    return Path(f"{path}.lock")


@contextmanager
def file_lock(path: Path, timeout: float = 10.0, poll_interval: float = 0.05, stale_after: float = 300.0) -> Iterator[None]:
    """Acquire cross-platform lock via atomic lockfile creation."""
    lock_path = _lock_path_for(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(timeout, 0.0)
    fd = None

    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            payload = {"pid": os.getpid(), "created_at": time.time(), "target": str(path)}
            os.write(fd, (json.dumps(payload) + "\n").encode())
            break
        except FileExistsError:
            # Best-effort stale lock cleanup for crashed writers.
            try:
                age = time.time() - lock_path.stat().st_mtime
                if stale_after is not None and age > stale_after:
                    lock_path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue

            if time.monotonic() >= deadline:
                raise LockTimeoutError(f"Timeout waiting for lock: {lock_path}")
            time.sleep(max(poll_interval, 0.01))

    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        lock_path.unlink(missing_ok=True)


def atomic_write_json(path: Path, payload: Any, timeout: float = 10.0) -> None:
    """Write JSON atomically under cross-platform lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with file_lock(path, timeout=timeout):
        with open(tmp, "w") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        tmp.replace(path)
