"""Regression tests for transactional phases and immutable chapter history."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import FakeAdapter  # type: ignore
from runner.book import run_book  # type: ignore
from runner.chapter import run_chapter  # type: ignore
from runner.filesystem import load_state_summary, scaffold_project  # type: ignore
from runner.phases import run_phase  # type: ignore

YES = "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: []\nvs_previous: none\nvs_anchor: none\n```\n"
NO = YES.replace("turn_page: yes", "turn_page: no")
INTAKE = (
    "=== FILE: ASSUMPTIONS.md ===\n# Assumptions\n\nnew\n"
    "=== FILE: artifacts/00-brief.md ===\n# Brief\n\nnew\n"
    "=== FILE: artifacts/01-market-map.md ===\n# Map\n\nnew\n"
    "=== FILE: artifacts/02-story-engine.md ===\n# Engine\n\nnew\n"
)


class RuntimeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="book-genesis-integrity-"))
        scaffold_project(self.project, idea="idea", adapter="fake", model_name="fake")

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def test_partial_retry_does_not_publish_or_advance_using_old_outputs(self):
        result = run_phase(self.project, {"architect": FakeAdapter([INTAKE])}, {"architect": ""})
        self.assertTrue(result.ok)
        old = (self.project / "artifacts" / "01-market-map.md").read_text(encoding="utf-8")
        state = self.project / "PROJECT_STATE.yaml"
        state.write_text(state.read_text(encoding="utf-8").replace("Phase 1: Foundation", "Phase 0: Intake"), encoding="utf-8")
        partial = INTAKE.split("=== FILE: artifacts/01-market-map.md ===")[0]
        result = run_phase(self.project, {"architect": FakeAdapter([partial])}, {"architect": ""})
        self.assertFalse(result.ok)
        self.assertEqual(old, (self.project / "artifacts" / "01-market-map.md").read_text(encoding="utf-8"))
        self.assertEqual("Phase 0: Intake", load_state_summary(self.project)["current_phase"])
        self.assertTrue(list((self.project / "work" / "phase-attempts").glob("*/*/STATUS.txt")))

    def test_publish_failure_rolls_back_every_artifact(self):
        for name in ("00-brief.md", "01-market-map.md", "02-story-engine.md"):
            (self.project / "artifacts" / name).write_text(f"old-{name}", encoding="utf-8")
        original_replace = __import__("os").replace
        calls = {"n": 0}
        def fail_second(source, destination):
            if str(destination).endswith("artifacts\\01-market-map.md"):
                raise OSError("injected publish failure")
            return original_replace(source, destination)
        with patch("runner.phases.os.replace", side_effect=fail_second):
            result = run_phase(self.project, {"architect": FakeAdapter([INTAKE])}, {"architect": ""})
        self.assertFalse(result.ok)
        self.assertEqual("old-00-brief.md", (self.project / "artifacts" / "00-brief.md").read_text(encoding="utf-8"))
        self.assertEqual("old-01-market-map.md", (self.project / "artifacts" / "01-market-map.md").read_text(encoding="utf-8"))

    def test_rewrite_keeps_prior_attempt_and_manifest_binds_accepted_verdict(self):
        outline = "## Chapter 1: One\n\nBeat.\n"
        (self.project / "artifacts" / "05-outline.md").write_text(outline, encoding="utf-8")
        adapters = {"writer": FakeAdapter(["# Chapter 1\n\nfirst\n", "# Chapter 1\n\nsecond\n"]), "judge": FakeAdapter([YES, YES])}
        first = run_chapter(self.project, 1, adapters)
        second = run_chapter(self.project, 1, adapters)
        self.assertTrue(first.accepted and second.accepted)
        drafts = self.project / "manuscript" / "drafts" / "chapter-01"
        self.assertIn("first", (drafts / "draft-1.md").read_text(encoding="utf-8"))
        self.assertIn("second", (drafts / "attempt-000002-draft-1.md").read_text(encoding="utf-8"))
        manifest = json.loads((self.project / "manuscript" / "chapters" / "history" / "chapter-01" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(2, len(manifest["attempts"]))
        self.assertEqual("attempt-000002", manifest["accepted"]["attempt_id"])

    def test_invalid_book_range_fails_before_writer_call(self):
        (self.project / "artifacts" / "05-outline.md").write_text("## Chapter 1: One\n", encoding="utf-8")
        writer = FakeAdapter(["# Chapter 1\n\ntext\n"])
        with self.assertRaises(ValueError):
            run_book(self.project, {"writer": writer, "judge": FakeAdapter([YES])}, {}, start=2, end=2)
        self.assertEqual([], writer.calls)

    def test_accepted_polish_stays_accepted_when_a_revision_is_worse(self):
        path = self.project / "manuscript" / "chapters" / "chapter-01.md"
        path.write_text("# Chapter 1\n\noriginal\n", encoding="utf-8")
        worse = "# Chapter 1\n\nworse\n"
        result = run_chapter(self.project, 1, {"judge": FakeAdapter([YES.replace("flags: []", "flags: [voice]"), YES.replace("vs_previous: none", "vs_previous: worse")]), "editor": FakeAdapter([worse])}, seed_draft=path.read_text(encoding="utf-8"), revise_on_flags=True)
        self.assertTrue(result.accepted)
        self.assertIn("original", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
