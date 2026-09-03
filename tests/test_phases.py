from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import FakeAdapter  # type: ignore  # noqa: E402
from runner.filesystem import load_state_summary, scaffold_project  # type: ignore  # noqa: E402
from runner.phases import run_phase, split_files  # type: ignore  # noqa: E402


INTAKE_RESPONSE = """Here is the intake.

=== FILE: ASSUMPTIONS.md ===
# Assumptions

Inferred: thriller, English, 80k words.

=== FILE: artifacts/00-brief.md ===
# Brief

BRIEF-SENTINEL a night-shift analyst in Brussels.

=== FILE: artifacts/01-market-map.md ===
```markdown
# Market Map

MARKET-SENTINEL
```

=== FILE: artifacts/02-story-engine.md ===
# Story Engine

ENGINE-SENTINEL

=== STATE ===
title: The Watch Room
genre: thriller
audience: adult readers of literary thrillers
language: en
target_length: 80000 words
"""

FOUNDATION_RESPONSE = """=== FILE: artifacts/03-characters.md ===
# Characters

CHARACTERS-SENTINEL

=== FILE: artifacts/04-theme.md ===
# Theme

THEME-SENTINEL

=== FILE: artifacts/06-emotional-curve.md ===
# Emotional Curve

CURVE-SENTINEL
"""


class SplitFilesTests(unittest.TestCase):
    def test_splits_named_files_and_the_state_block(self) -> None:
        files, state = split_files(INTAKE_RESPONSE)
        self.assertEqual(
            {"ASSUMPTIONS.md", "artifacts/00-brief.md", "artifacts/01-market-map.md", "artifacts/02-story-engine.md"},
            set(files),
        )
        self.assertIn("BRIEF-SENTINEL", files["artifacts/00-brief.md"])
        self.assertTrue(files["artifacts/01-market-map.md"].startswith("# Market Map"))
        self.assertEqual("thriller", state["genre"])
        self.assertEqual("The Watch Room", state["title"])


class RunPhaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = Path(tempfile.mkdtemp(prefix="book-genesis-phase-"))
        scaffold_project(
            self.project,
            idea="a night-shift analyst in Brussels notices nine regions moving in lockstep",
            adapter="fake",
            model_name="fake",
            language="en",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.project, ignore_errors=True)

    def test_intake_writes_outputs_updates_state_and_advances(self) -> None:
        adapter = FakeAdapter([INTAKE_RESPONSE])
        result = run_phase(self.project, {"architect": adapter}, {"architect": ""})

        self.assertTrue(result.ok, msg=str(result.pending))
        prompt = adapter.calls[0].prompt
        self.assertIn("night-shift analyst in Brussels", prompt)
        self.assertIn("Intake Rules", prompt)
        self.assertIn("BRIEF-SENTINEL", (self.project / "artifacts" / "00-brief.md").read_text(encoding="utf-8"))
        summary = load_state_summary(self.project)
        self.assertEqual("Phase 1: Foundation", summary["current_phase"])
        self.assertEqual("thriller", summary["genre"])
        self.assertEqual("The Watch Room", summary["title"])

    def test_missing_required_output_does_not_advance(self) -> None:
        partial = INTAKE_RESPONSE.split("=== FILE: artifacts/01-market-map.md ===")[0]
        result = run_phase(self.project, {"architect": FakeAdapter([partial])}, {"architect": ""})

        self.assertFalse(result.ok)
        self.assertIn("artifacts/01-market-map.md", result.pending)
        self.assertEqual("Phase 0: Intake", load_state_summary(self.project)["current_phase"])

    def test_later_phase_sees_the_earlier_artifacts(self) -> None:
        run_phase(self.project, {"architect": FakeAdapter([INTAKE_RESPONSE])}, {"architect": ""})
        adapter = FakeAdapter([FOUNDATION_RESPONSE])
        result = run_phase(self.project, {"architect": adapter}, {"architect": ""})

        self.assertTrue(result.ok, msg=str(result.pending))
        prompt = adapter.calls[0].prompt
        self.assertIn("BRIEF-SENTINEL", prompt)
        self.assertIn("ENGINE-SENTINEL", prompt)
        self.assertIn("Foundation Rules", prompt)
        self.assertEqual("Phase 2: Architecture", load_state_summary(self.project)["current_phase"])

    def test_drafting_phase_is_not_run_here(self) -> None:
        run_phase(self.project, {"architect": FakeAdapter([INTAKE_RESPONSE])}, {"architect": ""})
        run_phase(self.project, {"architect": FakeAdapter([FOUNDATION_RESPONSE])}, {"architect": ""})
        outline = (
            "=== FILE: artifacts/05-outline.md ===\n# Outline\n\n## Chapter 1: The Watch Room\n\nBeats.\n\n"
            "=== FILE: artifacts/07-opening-strategy.md ===\n# Opening Strategy\n\nOPENING-SENTINEL\n"
        )
        run_phase(self.project, {"architect": FakeAdapter([outline])}, {"architect": ""})
        self.assertEqual("Phase 3: Drafting", load_state_summary(self.project)["current_phase"])

        with self.assertRaises(ValueError):
            run_phase(self.project, {"architect": FakeAdapter(["anything"])}, {"architect": ""})


if __name__ == "__main__":
    unittest.main()
