import json
import tempfile
import threading
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
    verify_packet_detailed,
    write_commit,
    write_project_checkpoint,
)


class DclTests(unittest.TestCase):
    def _seed_two_commits(self, root: Path) -> None:
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

    def test_commit_chain_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_two_commits(root)
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

    def test_delete_commit_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_two_commits(root)
            (root / ".governance" / "dcl" / "packets" / "PKT-1" / "commits" / "000001.json").unlink()
            ok, issues = verify_packet(root, "PKT-1")
            self.assertFalse(ok)
            self.assertTrue(any("seq mismatch" in item for item in issues))

    def test_reordered_sequence_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_two_commits(root)
            c1 = root / ".governance" / "dcl" / "packets" / "PKT-1" / "commits" / "000001.json"
            c2 = root / ".governance" / "dcl" / "packets" / "PKT-1" / "commits" / "000002.json"
            p1 = json.loads(c1.read_text())
            p2 = json.loads(c2.read_text())
            p1["seq"], p2["seq"] = p2["seq"], p1["seq"]
            c1.write_text(json.dumps(p1, indent=2) + "\n")
            c2.write_text(json.dumps(p2, indent=2) + "\n")
            ok, issues = verify_packet(root, "PKT-1")
            self.assertFalse(ok)
            self.assertTrue(any("seq mismatch" in item for item in issues))

    def test_runtime_state_mismatch_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_two_commits(root)
            detail = verify_packet_detailed(root, "PKT-1", state_packet={"status": "failed"})
            self.assertTrue(any("runtime state mismatch" in item for item in detail["issues"]))

    def test_concurrent_write_commit_seq_unique(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "constitution.md").write_text("constitution")
            failures = []

            def _writer(idx: int) -> None:
                try:
                    write_commit(
                        repo_root=root,
                        packet_id="PKT-C",
                        action=f"note-{idx}",
                        actor="codex",
                        pre_state={},
                        post_state={},
                    )
                except Exception as exc:  # pragma: no cover - explicit failure capture
                    failures.append(str(exc))

            threads = [threading.Thread(target=_writer, args=(i,)) for i in range(20)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertFalse(failures, failures)
            root_dir = root / ".governance" / "dcl" / "packets" / "PKT-C" / "commits"
            files = sorted(root_dir.glob("*.json"))
            self.assertEqual(len(files), 20)
            seqs = [json.loads(path.read_text())["seq"] for path in files]
            self.assertEqual(sorted(seqs), list(range(1, 21)))

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
