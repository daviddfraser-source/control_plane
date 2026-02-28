import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from governed_platform.governance.engine import GovernanceEngine
from governed_platform.governance.state_manager import StateManager


class OntologyValidationTests(unittest.TestCase):
    def test_deterministic_ontology_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path.parent
            docs_dir = repo_root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            schema = {
                "entities": {
                    "packet": {"anti_conflations": ["work_area"]},
                    "program": {"anti_conflations": []},
                },
                "vocabulary": {
                    "milestone": {"anti_aliases": ["deliverable"]},
                },
                "relationships": [
                    {"from": "program", "relation": "CONTAINS", "to": "packet", "invertible": False},
                ],
                "invariants": [
                    {"id": "INV_001", "assertion": "deterministic check", "severity": "error"},
                ],
            }
            (docs_dir / "ontology.json").write_text(json.dumps(schema, indent=2) + "\n")
            (docs_dir / "ontology.md").write_text("# ontology\n")

            state_path = tmp_path / "wbs-state.json"
            definition = {
                "metadata": {"project_name": "onto", "approved_by": "test", "approved_at": "2026-02-28"},
                "work_areas": [{"id": "A-0", "title": "Area"}],
                "packets": [{"id": "PKT-1", "wbs_ref": "1.1", "area_id": "A-0", "title": "Pkt", "scope": "subpacket deliverable work_area program contains packet packet contains program"}],
                "dependencies": {},
            }
            sm = StateManager(state_path)
            state = sm.default_state()
            state["packets"]["PKT-1"] = {
                "status": "in_progress",
                "assigned_to": "codex",
                "started_at": None,
                "completed_at": None,
                "notes": "deliverable work_area program contains packet packet contains program",
                "ontology_assertions": {"INV_001": False},
            }
            sm.save(state)
            engine = GovernanceEngine(definition, sm)
            ok, payload = engine.ontology_validate("PKT-1")
            self.assertTrue(ok, payload)

            checks = payload["checks"]
            by_kind = {}
            for entry in checks:
                by_kind.setdefault(entry["kind"], []).append(entry)

            # word-boundary behavior: "packet" in "subpacket" does not count, but explicit packet token does
            entity_checks = by_kind["entity_reference"]
            self.assertTrue(any(item["target"] == "packet" and item["ok"] for item in entity_checks))

            anti_alias = by_kind["anti_alias"]
            self.assertTrue(any(not item["ok"] for item in anti_alias))

            anti_conflation = by_kind["anti_conflation"]
            self.assertTrue(any(not item["ok"] for item in anti_conflation))

            inversion = by_kind["relationship_inversion"]
            self.assertTrue(any(not item["ok"] for item in inversion))

            invariant = by_kind["invariant"]
            self.assertTrue(any(item["target"] == "INV_001" and not item["ok"] for item in invariant))


if __name__ == "__main__":
    unittest.main()

