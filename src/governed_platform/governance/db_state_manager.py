import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class DatabaseStateManager:
    """
    SQLite-backed state manager with StateManager-compatible load/save methods.

    Postgres is intentionally deferred to adapter parity work; this class defines
    the transaction contract used by GovernanceEngine integration.
    """

    def __init__(self, db_path: Path, workspace: str = "default"):
        self.db_path = Path(db_path)
        self.workspace = workspace
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS governance_state (
                    workspace TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def default_state(self) -> Dict[str, Any]:
        return {
            "version": "1.0",
            "schema_version": "1.2",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "packets": {},
            "log": [],
            "area_closeouts": {},
            "log_integrity_mode": "plain",
            "templates": {},
            "template_usage": {},
            "ontology": {
                "enabled": False,
                "version": "0.0",
                "proposals": [],
                "history": [],
                "last_drift_scan_at": None,
            },
            "governance_config": {
                "preflight_required_default": False,
                "preflight_timeout_seconds": 3600,
                "heartbeat_interval_seconds": 900,
                "stall_multiplier": 2,
                "review_required_default": False,
                "max_review_cycles": 3,
                "review_agent_policy": "any_different_agent",
                "ontology_enabled": False,
            },
        }

    def load(self) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM governance_state WHERE workspace = ?",
                (self.workspace,),
            ).fetchone()
            if not row:
                return self.default_state()
            return json.loads(row["payload"])

    def save(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = datetime.now().isoformat()
        payload = json.dumps(state, separators=(",", ":"))
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO governance_state(workspace, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(workspace) DO UPDATE SET
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
                """,
                (self.workspace, payload, state["updated_at"]),
            )
            conn.commit()

    def save_without_lock(self, state: Dict[str, Any]) -> None:
        self.save(state)

