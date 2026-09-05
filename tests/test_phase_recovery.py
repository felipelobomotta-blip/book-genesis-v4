from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import json
import base64
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runner.adapters import FakeAdapter  # type: ignore
from runner.filesystem import scaffold_project  # type: ignore
from runner.phases import _begin_publication, recover_pending_publication, run_phase  # type: ignore

RESPONSE = (
    "=== FILE: ASSUMPTIONS.md ===\n# Assumptions\n\nnew\n"
    "=== FILE: artifacts/00-brief.md ===\n# Brief\n\nnew\n"
    "=== FILE: artifacts/01-market-map.md ===\n# Map\n\nnew\n"
    "=== FILE: artifacts/02-story-engine.md ===\n# Engine\n\nnew\n"
    "=== STATE ===\ntitle: New title\n"
)


class PhaseRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="phase-recovery-"))
        scaffold_project(self.project, idea="x", adapter="fake", model_name="fake")

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def test_state_write_failure_rolls_back_artifacts_and_state(self):
        before = (self.project / "PROJECT_STATE.yaml").read_bytes()
        with patch("runner.phases.update_state_value", side_effect=OSError("state disk full")):
            result = run_phase(self.project, {"architect": FakeAdapter([RESPONSE])}, {"architect": ""})
        self.assertFalse(result.ok)
        self.assertEqual(before, (self.project / "PROJECT_STATE.yaml").read_bytes())
        self.assertIn("BOOK_GENESIS_TEMPLATE", (self.project / "artifacts" / "00-brief.md").read_text(encoding="utf-8"))
        self.assertFalse((self.project / "work" / "phase-publication.json").exists())

    def test_abandoned_journal_recovers_idempotently(self):
        target = self.project / "artifacts" / "00-brief.md"
        before = target.read_bytes()
        staged = self.project / "work" / "stage"
        staged.mkdir(parents=True)
        (staged / "artifacts").mkdir()
        (staged / "artifacts" / "00-brief.md").write_text("new", encoding="utf-8")
        _begin_publication(self.project, staged, ["artifacts/00-brief.md"])
        target.write_text("half-published", encoding="utf-8")
        self.assertTrue(recover_pending_publication(self.project))
        self.assertEqual(before, target.read_bytes())
        self.assertFalse(recover_pending_publication(self.project))

    def test_invalid_journal_is_validated_before_restoring_any_file(self):
        target = self.project / "artifacts/00-brief.md"
        before = target.read_bytes()
        journal = self.project / "work/phase-publication.json"
        journal.parent.mkdir(exist_ok=True)
        for illegal, payload in [("README.md", ""), ("ASSUMPTIONS.md", "not base64!")]:
            journal.write_text(json.dumps({"version": 1, "targets": ["artifacts/00-brief.md", illegal], "snapshots": {
                "artifacts/00-brief.md": {"exists": True, "data": base64.b64encode(b"altered").decode()},
                illegal: {"exists": True, "data": payload},
            }}), encoding="utf-8")
            with self.assertRaises(ValueError):
                recover_pending_publication(self.project)
            self.assertEqual(before, target.read_bytes())


if __name__ == "__main__":
    unittest.main()
