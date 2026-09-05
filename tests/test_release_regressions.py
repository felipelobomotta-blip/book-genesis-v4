"""Release gates for checkpoint recovery and immutable runtime state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import AdapterError, FakeAdapter  # type: ignore  # noqa: E402
from runner.chapter import run_chapter  # type: ignore  # noqa: E402
from runner.filesystem import load_state_summary, scaffold_project, update_state_value  # type: ignore  # noqa: E402
from runner.phases import run_phase  # type: ignore  # noqa: E402
from runner.roles import build_role_adapters  # type: ignore  # noqa: E402
from runner.score import genesis_score  # type: ignore  # noqa: E402
from runner.session import run_session  # type: ignore  # noqa: E402


YES = """```yaml
turn_page: yes
stopped_at: none
remember:
  - the hum
flags: []
vs_previous: none
vs_anchor: none
```
"""

INTAKE = """=== FILE: ASSUMPTIONS.md ===
# Assumptions

new
=== FILE: artifacts/00-brief.md ===
# Brief

brief
=== FILE: artifacts/01-market-map.md ===
# Map

map
=== FILE: artifacts/02-story-engine.md ===
# Engine

engine
=== STATE ===
title: One
genre: thriller
language: en
"""

FOUNDATION = """=== FILE: artifacts/03-characters.md ===
# Characters

characters
=== FILE: artifacts/04-theme.md ===
# Theme

theme
=== FILE: artifacts/06-emotional-curve.md ===
# Curve

curve
"""

ARCHITECTURE = """=== FILE: artifacts/05-outline.md ===
# Outline

## Chapter 1: One

Beat.
=== FILE: artifacts/07-opening-strategy.md ===
# Opening

opening
"""

DRAFT = "# Chapter 1: One\n\nA draft that holds.\n"
AUDIT = "=== FILE: artifacts/08-adversarial-audit.md ===\n# Audit\n\naudit\n\naudit_status: pass\n"
SCORE = "=== FILE: artifacts/09-genesis-score-codex.md ===\n# Diagnostic\n\nscore\n"
PACKAGE = "=== FILE: artifacts/10-editorial-package.md ===\n# Package\n\npackage\n"
SEPARATOR = "\n=== NEXT ===\n"


class RecordingView:
    interactive = True

    def __init__(self, answers=()):
        self.answers = list(answers)
        self.checkpoints = []

    def header(self, **_kwargs):
        pass

    def stage_start(self, *_args, **_kwargs):
        pass

    def stage_update(self, *_args, **_kwargs):
        pass

    def stage_done(self, *_args, **_kwargs):
        pass

    def stage_fail(self, *_args, **_kwargs):
        pass

    def stage_stop(self, *_args, **_kwargs):
        pass

    def event(self, *_args, **_kwargs):
        pass

    def checkpoint(self, title, body, hint):
        self.checkpoints.append((title, body, hint))
        return self.answers.pop(0) if self.answers else ""

    def score(self, *_args, **_kwargs):
        pass

    def finish(self, *_args, **_kwargs):
        pass

    def fail(self, *_args, **_kwargs):
        pass


class ReleaseRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-release-"))
        self.project = self.tempdir / "book"
        scaffold_project(self.project, idea="idea", adapter="fake", model_name="fake", language="en")

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_chapter_one_checkpoint_reappears_once_after_resume(self):
        responses = [INTAKE, FOUNDATION, ARCHITECTURE, DRAFT, DRAFT, YES, YES, YES, AUDIT, SCORE, PACKAGE]
        response_path = self.tempdir / "responses.txt"
        response_path.write_text(SEPARATOR.join(responses), encoding="utf-8")
        setup = build_role_adapters(fake_responses_path=response_path)

        stopped = run_session(self.project, setup, RecordingView(["", "", "q"]))
        resumed = RecordingView([""])
        finished = run_session(self.project, setup, resumed)

        self.assertEqual("stopped", stopped.status)
        self.assertEqual("completed", finished.status)
        self.assertEqual(["Chapter 1, read blind"], [checkpoint[0] for checkpoint in resumed.checkpoints])

    def test_tampered_canonical_does_not_count_as_accepted_or_first_pass(self):
        canonical = self.project / "manuscript" / "chapters" / "chapter-01.md"
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text("# Chapter 1\n\naccepted\n", encoding="utf-8")
        digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
        draft = self.project / "manuscript" / "drafts" / "chapter-01" / "attempt-000001-draft-1.md"
        draft.parent.mkdir(parents=True)
        draft.write_text(canonical.read_text(encoding="utf-8"), encoding="utf-8")
        verdict = self.project / "evaluations" / "chapter-01-judge-attempt-000001-1.md"
        verdict.parent.mkdir(parents=True, exist_ok=True)
        verdict.write_text(YES, encoding="utf-8")
        accepted = {
            "attempt_id": "attempt-000001",
            "sequence": 1,
            "status": "accepted",
            "draft_path": "manuscript/drafts/chapter-01/attempt-000001-draft-1.md",
            "verdict_path": "evaluations/chapter-01-judge-attempt-000001-1.md",
            "sha256": digest,
        }
        manifest = self.project / "manuscript" / "chapters" / "history" / "chapter-01" / "manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"schema_version": "book-genesis.chapter-history/v1", "chapter": 1, "accepted": accepted, "attempts": [accepted]}), encoding="utf-8")
        (self.project / "RUN_REPORT.md").write_text(
            "# Run Report\n\n## Chapter log\n\n- chapter 1: accepted after 0 revision cycle(s); judge: fake; last verdict: turn_page=yes, flags=[], stopped_at=none; file: x\n",
            encoding="utf-8",
        )
        canonical.write_text("# Chapter 1\n\ntampered\n", encoding="utf-8")

        card = genesis_score(self.project)
        components = {component.key: component for component in card.components}
        self.assertEqual([1], card.blocked)
        self.assertEqual(0.0, components["accepted"].value)
        self.assertEqual(0.0, components["first_pass"].value)
        self.assertNotIn("1 of 1 chapters accepted in the end", card.markdown())

    def test_judge_failure_leaves_hashed_draft_reference_in_pending_attempt(self):
        (self.project / "artifacts" / "05-outline.md").write_text("## Chapter 1: One\n", encoding="utf-8")
        with self.assertRaises(AdapterError):
            run_chapter(
                self.project,
                1,
                {"writer": FakeAdapter(["# Chapter 1\n\ninspectable draft\n"]), "judge": FakeAdapter()},
            )

        manifest = json.loads((self.project / "manuscript" / "chapters" / "history" / "chapter-01" / "manifest.json").read_text(encoding="utf-8"))
        attempt = manifest["attempts"][0]
        self.assertEqual("drafted", attempt["status"])
        draft = self.project / attempt["draft_path"]
        self.assertTrue(draft.is_file())
        self.assertEqual(hashlib.sha256(draft.read_bytes()).hexdigest(), attempt["sha256"])

    def test_publish_failure_restores_all_outputs_and_state(self):
        self.assertTrue(run_phase(self.project, {"architect": FakeAdapter([INTAKE])}, {"architect": ""}).ok)
        update_state_value(self.project / "PROJECT_STATE.yaml", "current_phase", "Phase 0: Intake")
        old = {relative: (self.project / relative).read_text(encoding="utf-8") for relative in ("ASSUMPTIONS.md", "artifacts/00-brief.md", "artifacts/01-market-map.md", "artifacts/02-story-engine.md")}
        replacement = INTAKE.replace("new", "replacement")
        original_replace = __import__("os").replace
        calls = {"count": 0}

        def fail_second(source, destination):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("injected publish failure")
            return original_replace(source, destination)

        with patch("runner.phases.os.replace", side_effect=fail_second):
            result = run_phase(self.project, {"architect": FakeAdapter([replacement])}, {"architect": ""})

        self.assertFalse(result.ok)
        self.assertEqual("Phase 0: Intake", load_state_summary(self.project)["current_phase"])
        self.assertEqual(old, {relative: (self.project / relative).read_text(encoding="utf-8") for relative in old})


if __name__ == "__main__":
    unittest.main()
