#!/usr/bin/env python3
"""State migration runner for governed platform state files."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from governed_platform.governance.migrations.runner import migrate_state, LATEST_VERSION


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".governance/wbs-state.json")
    if not target.exists():
        print(f"State file not found: {target}")
        sys.exit(1)

    state = json.loads(target.read_text())
    before = state.get("version", "legacy")
    migrated = migrate_state(state)
    after = migrated.get("version", "unknown")
    target.write_text(json.dumps(migrated, indent=2) + "\n")
    print(f"Migrated {target}: {before} -> {after} (latest={LATEST_VERSION})")


if __name__ == "__main__":
    main()
