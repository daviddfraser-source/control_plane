from datetime import datetime
from typing import Dict, Any


def migrate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade legacy unversioned state to 1.0."""
    state.setdefault("version", "1.0")
    state.setdefault("created_at", datetime.now().isoformat())
    state.setdefault("updated_at", datetime.now().isoformat())
    state.setdefault("packets", {})
    state.setdefault("log", [])
    state.setdefault("area_closeouts", {})
    return state
