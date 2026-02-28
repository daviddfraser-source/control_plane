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


class GovernanceSmokeTests(unittest.TestCase):
    def test_engine_claim_and_done_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "wbs-state.json"
            definition = {
                "metadata": {"project_name": "smoke", "approved_by": "test", "approved_at": "2026-02-28"},
                "work_areas": [{"id": "A-0", "title": "Area"}],
                "packets": [
                    {
                        "id": "PKT-1",
                        "wbs_ref": "1.1",
                        "area_id": "A-0",
                        "title": "Packet 1",
                        "scope": "smoke scope",
                    }
                ],
                "dependencies": {},
            }
            sm = StateManager(state_path)
            state = sm.default_state()
            state["packets"]["PKT-1"] = {
                "status": "pending",
                "assigned_to": None,
                "started_at": None,
                "completed_at": None,
                "notes": None,
            }
            sm.save(state)
            engine = GovernanceEngine(definition, sm)

            ok, msg = engine.claim("PKT-1", "codex")
            self.assertTrue(ok, msg)
            ok, msg = engine.done("PKT-1", "codex", "smoke evidence")
            self.assertTrue(ok, msg)
            self.assertEqual(engine.status()["packets"]["PKT-1"]["status"], "done")


if __name__ == "__main__":
    unittest.main()
