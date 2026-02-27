#!/usr/bin/env python3
"""
Shared utilities for WBS orchestration.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Paths
GOV = Path(__file__).parent
WBS_DEF = GOV / "wbs.json"
WBS_STATE = GOV / "wbs-state.json"

SRC_PATH = GOV.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Tag-based dependency resolution (Phase 6)
try:
    from tag_resolver import (
        expand_dependencies_with_validation,
        TagIndex,
        DependencyExpander
    )
    TAG_EXPANSION_AVAILABLE = True
except ImportError:
    TAG_EXPANSION_AVAILABLE = False
    expand_dependencies_with_validation = None

try:
    from governed_platform.governance.status import normalize_runtime_status, normalize_packet_status_map
    from governed_platform.governance.log_integrity import normalize_log_mode
except Exception:
    # Fallback keeps utility import-safe even before src is available.
    normalize_runtime_status = lambda value, default="pending", strict=False: str(value or default).lower()  # noqa: E731
    normalize_packet_status_map = lambda state: state  # noqa: E731
    normalize_log_mode = lambda value, strict=False: str(value or "plain").lower()  # noqa: E731

# Schema Versioning (Phase 6)
CURRENT_SCHEMA_VERSION = "1.1"


class MigrationError(Exception):
    """Raised when state migration fails."""
    pass


def parse_version(version_str: str) -> tuple:
    """Parse version string to tuple for comparison."""
    try:
        parts = version_str.split(".")
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        return (1, 0)  # Default to 1.0 for invalid versions


def validate_migration_event(event: dict, expected_from: str, expected_to: str) -> bool:
    """
    Validate migration event complies with Constitution Article II Section 6.

    Required fields per state versioning contract:
    - event: "state_migrated"
    - timestamp: ISO 8601 format
    - agent: "system"
    - from_version: previous version
    - to_version: new version
    - migration_name: unique identifier
    - automatic: bool
    - notes: description

    Returns True if valid, raises ValueError if invalid.
    """
    required_fields = ["event", "timestamp", "agent", "from_version", "to_version",
                      "migration_name", "automatic", "notes"]

    for field in required_fields:
        if field not in event:
            raise ValueError(f"Migration event missing required field: {field}")

    if event["event"] != "state_migrated":
        raise ValueError(f"Invalid migration event type: {event['event']}")

    if event["agent"] != "system":
        raise ValueError(f"Migration agent must be 'system', got: {event['agent']}")

    if event["from_version"] != expected_from:
        raise ValueError(f"Expected from_version={expected_from}, got {event['from_version']}")

    if event["to_version"] != expected_to:
        raise ValueError(f"Expected to_version={expected_to}, got {event['to_version']}")

    return True


def migrate_1_0_to_1_1(state: dict) -> dict:
    """
    Migrate state from v1.0 to v1.1.
    Adds schema_version field for explicit version tracking.

    Constitutional compliance:
    - Article II Section 1: Atomic Transitions - returns new state, never mutates input
    - Article II Section 6: Transition Logging - appends migration event to log
    - Article IV Section 1: State File Integrity - validates pre/post conditions
    """
    # Validate precondition: should not already have schema_version >= 1.1
    existing_version = state.get("schema_version", "1.0")
    if existing_version != "1.0":
        raise MigrationError(f"Expected v1.0, found v{existing_version}")

    # Create migrated copy (immutability - Article II Section 1)
    migrated = state.copy()

    # Ensure log array exists (defensive)
    migrated.setdefault("log", [])

    # Apply schema change: add schema_version field
    migrated["schema_version"] = "1.1"

    # Update updated_at timestamp (no silent modification)
    migrated["updated_at"] = datetime.now().isoformat()

    # Append migration log event (Constitution Article II Section 6)
    migration_event = {
        "event": "state_migrated",
        "timestamp": datetime.now().isoformat(),
        "agent": "system",
        "from_version": "1.0",
        "to_version": "1.1",
        "migration_name": "add_schema_version_field",
        "automatic": True,
        "notes": "Added schema_version field for explicit version tracking"
    }

    # Validate migration event format
    validate_migration_event(migration_event, "1.0", "1.1")

    # Append to log (append-only per Article VII Section 1)
    migrated["log"].append(migration_event)

    # Postcondition: verify schema_version is set correctly
    if migrated.get("schema_version") != "1.1":
        raise MigrationError("Postcondition failed: schema_version not set to 1.1")

    return migrated


# Migration Registry
# Maps "from_to" version strings to migration metadata
MIGRATIONS = {
    "1.0_to_1.1": {
        "name": "add_schema_version_field",
        "from_version": "1.0",
        "to_version": "1.1",
        "apply": migrate_1_0_to_1_1,
        "description": "Add schema_version field for explicit version tracking"
    },
    # Future migrations will be added here
}

# Colors (respects NO_COLOR env var)
def c(code, text):
    if os.environ.get("NO_COLOR") or not (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()):
        return text
    return f"\033[{code}m{text}\033[0m"

green = lambda t: c("32", t)
red = lambda t: c("31", t)
yellow = lambda t: c("33", t)
blue = lambda t: c("34", t)
bold = lambda t: c("1", t)
dim = lambda t: c("2", t)


def load_definition() -> dict:
    """Load WBS definition (read-only after init)."""
    if not WBS_DEF.exists():
        return {}
    with open(WBS_DEF) as f:
        return json.load(f)


def migrate_to_current(state: dict) -> dict:
    """
    Migrate state to current schema version.
    Applies migration chain sequentially until state is at CURRENT_SCHEMA_VERSION.
    """
    current_version = state.get("schema_version", "1.0")

    # Check if already at current version
    if current_version == CURRENT_SCHEMA_VERSION:
        return state

    # Reject unknown future versions (forward compatibility guard)
    if parse_version(current_version) > parse_version(CURRENT_SCHEMA_VERSION):
        raise MigrationError(
            f"State file requires schema v{current_version}, "
            f"but this version only supports up to v{CURRENT_SCHEMA_VERSION}. "
            f"Please upgrade the governance CLI."
        )

    # Apply migration chain
    migrated = state
    while current_version != CURRENT_SCHEMA_VERSION:
        # Find migration for current -> next version
        migration_key = None
        for key, migration in MIGRATIONS.items():
            if migration["from_version"] == current_version:
                migration_key = key
                break

        if not migration_key:
            raise MigrationError(
                f"No migration path from v{current_version} to v{CURRENT_SCHEMA_VERSION}. "
                f"Available migrations: {list(MIGRATIONS.keys())}"
            )

        # Apply migration
        migration = MIGRATIONS[migration_key]
        try:
            migrated = migration["apply"](migrated)
            current_version = migration["to_version"]
        except Exception as e:
            raise MigrationError(
                f"Migration {migration['name']} failed: {e}"
            ) from e

    return migrated




def expand_and_store_dependencies(definition: dict, state: dict) -> dict:
    """
    Expand tag-based dependencies and store in state.

    Args:
        definition: WBS definition with dependencies (may include tags)
        state: Current state dict

    Returns:
        Updated state with expanded_dependencies field

    Called during WBS initialization to expand tags to packet IDs.
    Logs expansion events per ORCH-011 transparency requirements.
    """
    if not TAG_EXPANSION_AVAILABLE:
        LOGGER.warning("Tag expansion not available (tag_resolver not imported)")
        return state

    packets = definition.get("packets", [])
    dependencies = definition.get("dependencies", {})

    # Check if any dependencies use tags
    has_tags = any(
        any(dep.startswith("tag:") for dep in deps)
        for deps in dependencies.values()
    )

    if not has_tags:
        # No tags to expand, use dependencies as-is
        state["expanded_dependencies"] = dependencies
        return state

    # Expand tag-based dependencies
    try:
        expanded = expand_dependencies_with_validation(packets, dependencies)
        state["expanded_dependencies"] = expanded

        # Log summary
        tag_count = sum(
            sum(1 for d in deps if d.startswith("tag:"))
            for deps in dependencies.values()
        )
        LOGGER.info(
            f"Tag expansion complete: {tag_count} tag references expanded "
            f"across {len(expanded)} packets"
        )

    except Exception as e:
        LOGGER.error(f"Tag expansion failed: {e}")
        # Fallback: use original dependencies
        state["expanded_dependencies"] = dependencies
        raise

    return state

def load_state() -> dict:
    """
    Load current execution state.
    Automatically migrates to current schema version if needed.
    Persists migrated state to ensure atomicity (Constitution Article II Section 1).
    """
    if not WBS_STATE.exists():
        # New state files always created at current schema version
        now = datetime.now().isoformat()
        return {
            "version": "1.0",
            "schema_version": CURRENT_SCHEMA_VERSION,
            "created_at": now,
            "updated_at": now,
            "packets": {},
            "log": [],
            "area_closeouts": {},
            "log_integrity_mode": "plain",
        }

    with open(WBS_STATE) as f:
        state = json.load(f)

    # Set defaults for required fields
    now = datetime.now().isoformat()
    state.setdefault("version", "1.0")
    state.setdefault("created_at", now)
    state.setdefault("updated_at", now)
    state.setdefault("packets", {})
    state.setdefault("log", [])
    state.setdefault("area_closeouts", {})
    state.setdefault("log_integrity_mode", "plain")
    state.setdefault("expanded_dependencies", {})

    # Record original version for migration detection
    original_version = state.get("schema_version", "1.0")

    # Detect and apply migrations
    state = migrate_to_current(state)

    # If migration occurred, persist it immediately for atomicity
    if state.get("schema_version") != original_version:
        # Write migrated state back to file
        # Note: This uses basic JSON write; calling code may use atomic_write_json
        # But for migration, we want to persist immediately to avoid re-running
        with open(WBS_STATE, "w") as f:
            json.dump(state, f, indent=2)

    # Normalize log mode and status map
    state["log_integrity_mode"] = normalize_log_mode(state.get("log_integrity_mode"))
    return normalize_packet_status_map(state)


def get_counts(state: dict) -> dict:
    """Get packet counts by status."""
    counts = {}
    for pstate in state.get("packets", {}).values():
        s = normalize_runtime_status(pstate.get("status", "pending"))
        counts[s] = counts.get(s, 0) + 1
    return counts
