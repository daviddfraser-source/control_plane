import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from governed_platform.governance.engine import GovernanceEngine
from governed_platform.governance.state_manager import StateManager


def _packet_state() -> dict:
    return {
        "status": "pending",
        "assigned_to": None,
        "started_at": None,
        "completed_at": None,
        "notes": None,
    }


class LifecycleTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.tmp.name) / "wbs-state.json"
        self.definition = {
            "metadata": {"project_name": "lifecycle", "approved_by": "test", "approved_at": "2026-02-28"},
            "work_areas": [{"id": "A-0", "title": "Area"}],
            "packets": [
                {
                    "id": "PF-1",
                    "wbs_ref": "1.1",
                    "area_id": "A-0",
                    "title": "Preflight approve",
                    "scope": "scope",
                    "preflight_required": True,
                },
                {
                    "id": "PF-2",
                    "wbs_ref": "1.2",
                    "area_id": "A-0",
                    "title": "Preflight return",
                    "scope": "scope",
                    "preflight_required": True,
                },
                {
                    "id": "HB-1",
                    "wbs_ref": "1.3",
                    "area_id": "A-0",
                    "title": "Heartbeat stall",
                    "scope": "scope",
                },
                {
                    "id": "RV-1",
                    "wbs_ref": "1.4",
                    "area_id": "A-0",
                    "title": "Review approve",
                    "scope": "scope",
                    "review_required": True,
                },
                {
                    "id": "RV-2",
                    "wbs_ref": "1.5",
                    "area_id": "A-0",
                    "title": "Review reject escalates",
                    "scope": "scope",
                    "review_required": True,
                },
            ],
            "dependencies": {},
        }
        sm = StateManager(self.state_path)
        state = sm.default_state()
        state["governance_config"]["max_review_cycles"] = 1
        for packet in self.definition["packets"]:
            state["packets"][packet["id"]] = _packet_state()
        sm.save(state)
        self.engine = GovernanceEngine(self.definition, sm)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_preflight_approve_and_return(self) -> None:
        ok, msg = self.engine.claim("PF-1", "alice")
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["PF-1"]["status"], "preflight")

        assessment = {
            "context_confirmation": {"ok": True},
            "ambiguity_register": [],
            "risk_flags": [],
            "execution_plan": {"steps": ["x"]},
        }
        ok, msg = self.engine.preflight("PF-1", "alice", assessment)
        self.assertTrue(ok, msg)
        ok, msg = self.engine.preflight_approve("PF-1", "supervisor")
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["PF-1"]["status"], "in_progress")

        ok, msg = self.engine.claim("PF-2", "alice")
        self.assertTrue(ok, msg)
        ok, msg = self.engine.preflight("PF-2", "alice", assessment)
        self.assertTrue(ok, msg)
        ok, msg = self.engine.preflight_return("PF-2", "supervisor", "needs clarification")
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["PF-2"]["status"], "pending")

    def test_heartbeat_stall_and_resume(self) -> None:
        ok, msg = self.engine.claim("HB-1", "alice")
        self.assertTrue(ok, msg)
        state = self.engine.status()
        state["packets"]["HB-1"]["started_at"] = (datetime.now() - timedelta(hours=2)).isoformat()
        self.engine.state_manager.save(state)  # deterministic test setup

        ok, msg = self.engine.check_stalled("HB-1")
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["HB-1"]["status"], "stalled")

        ok, msg = self.engine.heartbeat("HB-1", "alice", "recovering")
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["HB-1"]["status"], "in_progress")

    def test_review_two_person_integrity_and_escalation(self) -> None:
        ok, msg = self.engine.claim("RV-1", "exec")
        self.assertTrue(ok, msg)
        ok, msg = self.engine.done("RV-1", "exec", "evidence")
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["RV-1"]["status"], "review")

        ok, msg = self.engine.review_claim("RV-1", "exec")
        self.assertFalse(ok)
        self.assertIn("Two-person integrity", msg)

        ok, msg = self.engine.review_claim("RV-1", "reviewer")
        self.assertTrue(ok, msg)
        ok, msg = self.engine.review_submit(
            "RV-1",
            "reviewer",
            "APPROVE",
            {
                "exit_criteria_assessment": {"all": "pass"},
                "findings": "ok",
                "risk_flags": [],
            },
        )
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["RV-1"]["status"], "done")

        ok, msg = self.engine.claim("RV-2", "exec")
        self.assertTrue(ok, msg)
        ok, msg = self.engine.done("RV-2", "exec", "evidence")
        self.assertTrue(ok, msg)
        ok, msg = self.engine.review_claim("RV-2", "reviewer")
        self.assertTrue(ok, msg)
        ok, msg = self.engine.review_submit(
            "RV-2",
            "reviewer",
            "REJECT",
            {
                "exit_criteria_assessment": {"all": "fail"},
                "findings": "not met",
                "risk_flags": ["r1"],
            },
        )
        self.assertTrue(ok, msg)
        self.assertEqual(self.engine.status()["packets"]["RV-2"]["status"], "escalated")


if __name__ == "__main__":
    unittest.main()
