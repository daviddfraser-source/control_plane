import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from governed_platform.governance.dcl import (
    export_proof_bundle,
    verify_packet,
    write_commit,
    write_project_checkpoint,
)


class DclTests(unittest.TestCase):
    def test_commit_chain_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constitution.md").write_text("constitution")
            write_commit(
                repo_root=root,
                packet_id="PKT-1",
                action="claim",
                actor="codex",
                pre_state={"status": "pending"},
                post_state={"status": "in_progress"},
            )
            write_commit(
                repo_root=root,
                packet_id="PKT-1",
                action="done",
                actor="codex",
                pre_state={"status": "in_progress"},
                post_state={"status": "done"},
            )
            ok, issues = verify_packet(root, "PKT-1")
            self.assertTrue(ok, issues)

            # Tamper one commit
            commit = root / ".governance" / "dcl" / "packets" / "PKT-1" / "commits" / "000002.json"
            payload = json.loads(commit.read_text())
            payload["post_state_hash"] = "BAD"
            commit.write_text(json.dumps(payload, indent=2) + "\n")
            ok, issues = verify_packet(root, "PKT-1")
            self.assertFalse(ok)
            self.assertTrue(any("commit_hash mismatch" in item for item in issues))

    def test_checkpoint_and_proof_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constitution.md").write_text("constitution")
            commit = write_commit(
                repo_root=root,
                packet_id="PKT-1",
                action="claim",
                actor="codex",
                pre_state={"status": "pending"},
                post_state={"status": "in_progress"},
            )
            checkpoint = write_project_checkpoint(root, phase="PhaseA", packet_heads={"PKT-1": commit["commit_hash"]})
            self.assertIn("merkle_root", checkpoint)
            bundle = export_proof_bundle(root, "PKT-1", root / "proof.zip")
            self.assertTrue(bundle.exists())


if __name__ == "__main__":
    unittest.main()

