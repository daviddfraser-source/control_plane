from typing import Dict, Any


def migrate(state: Dict[str, Any]) -> Dict[str, Any]:
    """No-op migration for explicit 1.x baseline normalization."""
    state.setdefault("version", "1.0")
    state.setdefault("area_closeouts", {})
    state.setdefault("packets", {})
    state.setdefault("log", [])
    return state
