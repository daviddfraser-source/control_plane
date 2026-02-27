from typing import Dict, Any

from governed_platform.governance.migrations.v0_to_v1 import migrate as migrate_v0_to_v1
from governed_platform.governance.migrations.v1_to_v1 import migrate as migrate_v1_to_v1


LATEST_VERSION = "1.0"


def migrate_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate arbitrary known state shape to latest version."""
    version = state.get("version")
    if version is None:
        state = migrate_v0_to_v1(state)
        version = state.get("version")
    if version == "1.0":
        return migrate_v1_to_v1(state)
    raise ValueError(f"Unsupported state version: {version}")
