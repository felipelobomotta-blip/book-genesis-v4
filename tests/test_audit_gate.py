"""Release regressions for the adversarial-audit phase gate."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runner.adapters import FakeAdapter  # type: ignore  # noqa: E402
from runner.audit import audit_status  # type: ignore  # noqa: E402
from runner.app import session_main  # type: ignore  # noqa: E402
from runner.cli import EXIT_BLOCKED  # type: ignore  # noqa: E402
from runner.filesystem import advance_phase, load_state_summary, scaffold_project, update_state_value  # type: ignore  # noqa: E402
from runner.phases import run_phase  # type: ignore  # noqa: E402


def audit_response(body: str) -> str:
    return f"=== FILE: artifacts/08-adversarial-audit.md ===\n# Audit\n\n{body}\n"


# Frozen decisive wording from work/real-book-smoke/artifacts/08-adversarial-audit.md.
REAL_MAJOR_REPLAY = """## Veredito geral

**Veredito final: MAJOR REWRITE.**

Não se trata de polimento.
"""

INTAKE = """=== FILE: ASSUMPTIONS.md ===
# Assumptions

audit
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
title: Audit
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

beat
=== FILE: artifacts/07-opening-strategy.md ===
# Opening

opening
"""
DRAFT = "# Chapter 1: One\n\nA complete canonical chapter.\n"
YES = "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: []\nvs_previous: none\nvs_anchor: none\n```\n"
SEPARATOR = "\n=== NEXT ===\n"


class AuditGateTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-audit-gate-"))
        self.project = self.tempdir / "book"
        scaffold_project(self.project, idea="audit", adapter="fake", model_name="fake")
        (self.project / "artifacts" / "05-outline.md").write_text("## Chapter 1: One\n", encoding="utf-8")
        chapter = self.project / "manuscript" / "chapters" / "chapter-01.md"
        chapter.write_text("# Chapter 1\n\nCANONICAL-PROSE-SENTINEL\n", encoding="utf-8")
        update_state_value(self.project / "PROJECT_STATE.yaml", "current_phase", "Phase 4: Adversarial Audit")

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _run_audit(self, text: str):
        return run_phase(self.project, {"architect": FakeAdapter([audit_response(text)])}, {"architect": ""})

    def _gate_value(self, project: Path, gate: str) -> str:
        for line in (project / "PROJECT_STATE.yaml").read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{gate}:"):
                return line.split(":", 1)[1].strip().strip('"')
        self.fail(f"gate {gate} not found")

    def test_real_major_replay_is_blocked_and_preserves_canonical_prose(self):
        original = (self.project / "manuscript" / "chapters" / "chapter-01.md").read_bytes()
        result = self._run_audit(REAL_MAJOR_REPLAY)

        self.assertFalse(result.ok)
        self.assertIn("audit_status: major_rewrite", result.pending)
        self.assertEqual(original, (self.project / "manuscript" / "chapters" / "chapter-01.md").read_bytes())
        self.assertIn("MAJOR REWRITE", (self.project / "artifacts" / "08-adversarial-audit.md").read_text(encoding="utf-8"))
        state = load_state_summary(self.project)
        self.assertEqual("Phase 4: Adversarial Audit", state["current_phase"])
        self.assertEqual("awaiting_revision", state["status"])
        self.assertEqual("blocked", self._gate_value(self.project, "adversarial_audit"))
        self.assertIn("BOOK_GENESIS_TEMPLATE", (self.project / "artifacts" / "09-genesis-score-codex.md").read_text(encoding="utf-8"))
        self.assertIn("BOOK_GENESIS_TEMPLATE", (self.project / "artifacts" / "10-editorial-package.md").read_text(encoding="utf-8"))

    def test_revise_blocks_score_and_package(self):
        result = self._run_audit("audit_status: revise\n\nA structural revision is required.")

        self.assertFalse(result.ok)
        self.assertIn("audit_status: revise", result.pending)
        state = load_state_summary(self.project)
        self.assertEqual("Phase 4: Adversarial Audit", state["current_phase"])
        self.assertEqual("awaiting_revision", state["status"])
        self.assertIn("BOOK_GENESIS_TEMPLATE", (self.project / "artifacts" / "09-genesis-score-codex.md").read_text(encoding="utf-8"))
        self.assertIn("BOOK_GENESIS_TEMPLATE", (self.project / "artifacts" / "10-editorial-package.md").read_text(encoding="utf-8"))

    def test_explicit_pass_advances_to_final_score(self):
        result = self._run_audit("audit_status: pass\n\nNo blocking issue found.")

        self.assertTrue(result.ok)
        self.assertEqual("Phase 5: Final Score", load_state_summary(self.project)["current_phase"])
        self.assertEqual("passed", self._gate_value(self.project, "adversarial_audit"))

    def test_direct_advance_cannot_bypass_major_rewrite(self):
        artifact = self.project / "artifacts" / "08-adversarial-audit.md"
        artifact.write_text(REAL_MAJOR_REPLAY, encoding="utf-8")

        advanced = advance_phase(self.project)

        self.assertFalse(advanced["ok"])
        self.assertIn("audit_status: major_rewrite", advanced["pending"])
        state = load_state_summary(self.project)
        self.assertEqual("Phase 4: Adversarial Audit", state["current_phase"])
        self.assertEqual("awaiting_revision", state["status"])

    def test_missing_or_ambiguous_machine_status_never_publishes_or_advances(self):
        for text in (
            "Narrative audit without a machine-readable gate.",
            "audit_status: pass\naudit_status: revise",
            "audit_status: pass\naudit_status: withheld",
        ):
            with self.subTest(text=text):
                project = self.tempdir / f"case-{len(list(self.tempdir.iterdir()))}"
                shutil.copytree(self.project, project)
                result = run_phase(project, {"architect": FakeAdapter([audit_response(text)])}, {"architect": ""})
                self.assertFalse(result.ok)
                self.assertEqual("Phase 4: Adversarial Audit", load_state_summary(project)["current_phase"])
                self.assertIn("BOOK_GENESIS_TEMPLATE", (project / "artifacts" / "08-adversarial-audit.md").read_text(encoding="utf-8"))

    def test_audit_parser_requires_exactly_one_unambiguous_status(self):
        self.assertEqual("pass", audit_status("audit_status: pass"))
        self.assertEqual("pass", audit_status("audit_status: pass\r\n"))
        self.assertEqual("major_rewrite", audit_status(REAL_MAJOR_REPLAY))
        for text in (
            "audit_status: pass\naudit_status: revise",
            "audit_status: pass\naudit_status: withheld",
            "audit_status: pass\n" + REAL_MAJOR_REPLAY,
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    audit_status(text)

    def test_session_cli_returns_blocked_without_score_or_package(self):
        responses = [INTAKE, FOUNDATION, ARCHITECTURE, DRAFT, DRAFT, YES, YES, YES, audit_response(REAL_MAJOR_REPLAY)]
        response_path = self.tempdir / "responses.txt"
        response_path.write_text(SEPARATOR.join(responses), encoding="utf-8")
        project = self.tempdir / "session-book"
        view = SessionRecordingView()

        code = session_main(
            ["new", "--idea", "audit", "--language", "en", "--path", str(project), "--yes", "--fake-responses", str(response_path)],
            view=view,
        )

        self.assertEqual(EXIT_BLOCKED, code)
        self.assertEqual([], view.scores)
        self.assertNotIn("Score", view.started)
        self.assertNotIn("Package", view.started)
        self.assertEqual(["Audit"], view.stopped)
        self.assertIn("revision required", view.stop_messages[0].lower())
        self.assertIn("BOOK_GENESIS_TEMPLATE", (project / "artifacts" / "09-genesis-score-codex.md").read_text(encoding="utf-8"))
        self.assertIn("BOOK_GENESIS_TEMPLATE", (project / "artifacts" / "10-editorial-package.md").read_text(encoding="utf-8"))


class SessionRecordingView:
    interactive = True

    def __init__(self):
        self.started = []
        self.stopped = []
        self.stop_messages = []
        self.scores = []

    def header(self, **_kwargs): pass
    def stage_start(self, name, *_args): self.started.append(name)
    def stage_update(self, *_args): pass
    def stage_done(self, *_args): pass
    def stage_fail(self, *_args): pass
    def stage_stop(self, name, message):
        self.stopped.append(name)
        self.stop_messages.append(message)
    def event(self, *_args): pass
    def checkpoint(self, *_args): return ""
    def score(self, card): self.scores.append(card)
    def finish(self, *_args): pass
    def fail(self, *_args): pass


if __name__ == "__main__":
    unittest.main()
