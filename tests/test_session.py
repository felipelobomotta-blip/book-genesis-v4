"""The guided session runs the whole pipeline offline with the fake adapter (ADR 0009)."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.filesystem import scaffold_project  # type: ignore  # noqa: E402
from runner.roles import build_role_adapters  # type: ignore  # noqa: E402
from runner.session import interpret, run_session, strip_leading_heading  # type: ignore  # noqa: E402

OUTLINE = """# Outline

## Chapter 1: The Watch Room

OUTLINE-SENTINEL-CH1 Halden watches the dashboards and laughs.

## Chapter 2: The Drive

OUTLINE-SENTINEL-CH2 Halden drives Yusuf south.
"""
DRAFT = "# Chapter 1: The Watch Room\n\nDRAFT-SENTINEL Halden counted the hum. " + ("The console blinked. " * 20) + "\n"
DISRUPTED = DRAFT.replace("DRAFT-SENTINEL", "DISRUPTED-SENTINEL")
YES = "```yaml\nturn_page: yes\nstopped_at: none\nremember:\n  - the hum\nflags: []\nvs_previous: none\nvs_anchor: none\n```\n"
NO = "```yaml\nturn_page: no\nstopped_at: the second paragraph\nremember: []\nflags: [exposition]\nvs_previous: none\nvs_anchor: none\n```\n"
INTAKE = (
    "=== FILE: ASSUMPTIONS.md ===\n# Assumptions\n\nInferred: thriller.\n\n"
    "=== FILE: artifacts/00-brief.md ===\n# Brief\n\nBRIEF-SENTINEL\n\n"
    "=== FILE: artifacts/01-market-map.md ===\n# Market Map\n\nMARKET-SENTINEL\n\n"
    "=== FILE: artifacts/02-story-engine.md ===\n# Story Engine\n\nENGINE-SENTINEL\n\n"
    "=== STATE ===\ntitle: The Watch Room\ngenre: thriller\nlanguage: en\n"
)
INTAKE_DARKER = INTAKE.replace("BRIEF-SENTINEL", "BRIEF-DARKER")
FOUNDATION = (
    "=== FILE: artifacts/03-characters.md ===\n# Characters\n\nCHARACTERS-SENTINEL\n\n"
    "=== FILE: artifacts/04-theme.md ===\n# Theme\n\nTHEME-SENTINEL\n\n"
    "=== FILE: artifacts/06-emotional-curve.md ===\n# Curve\n\nCURVE-SENTINEL\n"
)
ARCHITECTURE = "=== FILE: artifacts/05-outline.md ===\n" + OUTLINE + "\n=== FILE: artifacts/07-opening-strategy.md ===\n# Opening\n\nOPENING-SENTINEL\n"
AUDIT = "=== FILE: artifacts/08-adversarial-audit.md ===\n# Audit\n\nAUDIT-SENTINEL\n"
SCORE = "=== FILE: artifacts/09-genesis-score-codex.md ===\n# Diagnostic\n\nSCORE-SENTINEL\n"
PACKAGE = "=== FILE: artifacts/10-editorial-package.md ===\n# Package\n\nPACKAGE-SENTINEL\n"
CHAPTER_ONE = [DRAFT, DISRUPTED, YES, YES, YES]  # writer, disruptor, three panel seats
CHAPTER_TWO = [DRAFT, DISRUPTED, YES]
SEPARATOR = "\n=== NEXT ===\n"


class RecordingView:
    """Every call the session makes, in order; answers to checkpoints are scripted."""

    def __init__(self, answers=None, interactive=True) -> None:
        self.answers = list(answers or [])
        self.interactive = interactive
        self.calls = []
        self.checkpoints = []
        self.card = None

    def header(self, **kwargs):
        self.calls.append(("header", kwargs))

    def stage_start(self, name, detail=""):
        self.calls.append(("start", name, detail))

    def stage_update(self, name, detail):
        self.calls.append(("update", name, detail))

    def stage_done(self, name, summary=""):
        self.calls.append(("done", name, summary))

    def stage_fail(self, name, message):
        self.calls.append(("fail", name, message))

    def stage_stop(self, name, message):
        self.calls.append(("stop", name, message))

    def event(self, line):
        self.calls.append(("event", line))

    def checkpoint(self, title, body, hint):
        self.checkpoints.append((title, body, hint))
        return self.answers.pop(0) if self.answers else ""

    def score(self, card):
        self.card = card
        self.calls.append(("score", card.score))

    def finish(self, paths):
        self.calls.append(("finish", dict(paths)))

    def fail(self, message):
        self.calls.append(("failed", message))

    def stages(self, kind):
        return [call[1] for call in self.calls if call[0] == kind]


class SessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-session-"))
        self.project = self.tempdir / "book"
        scaffold_project(self.project, idea="a night-shift analyst in Brussels", adapter="auto", model_name="auto", language="en")

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def setup_with(self, *responses: str):
        path = self.tempdir / "responses.txt"
        path.write_text(SEPARATOR.join(responses), encoding="utf-8")
        return build_role_adapters(fake_responses_path=path)

    def test_autonomous_run_goes_from_idea_to_score(self) -> None:
        setup = self.setup_with(INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE, *CHAPTER_TWO, AUDIT, SCORE, PACKAGE)
        view = RecordingView()

        result = run_session(self.project, setup, view, yes=True)

        self.assertEqual("completed", result.status, msg=view.calls)
        self.assertEqual(["Intake", "Foundation", "Architecture", "Drafting", "Audit", "Score", "Package"], view.stages("start"))
        self.assertEqual(["Intake", "Foundation", "Architecture", "Drafting", "Audit", "Score", "Package"], view.stages("done"))
        self.assertEqual([], view.checkpoints)  # --yes never asks
        header = view.calls[0][1]
        self.assertEqual("a night-shift analyst in Brussels", header["idea"])
        self.assertIn("writer", header["roles"])
        self.assertIn("panel", header["roles"])
        done = {call[1]: call[2] for call in view.calls if call[0] == "done"}
        self.assertEqual("The Watch Room, thriller", done["Intake"])
        self.assertEqual("2 chapters outlined", done["Architecture"])
        self.assertIn("2 chapters accepted", done["Drafting"])
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-02.md").exists())
        self.assertIsNotNone(view.card)
        self.assertEqual(10.0, view.card.score)  # 3/3 readers, both chapters first draft, both remembered
        self.assertIn("## Genesis Score", (self.project / "RUN_REPORT.md").read_text(encoding="utf-8"))
        events = [call[1] for call in view.calls if call[0] == "event"]
        self.assertTrue(any("chapter 1: judge says turn_page=yes" in line for line in events), msg=events[:10])

    def test_interactive_run_asks_three_times_and_shows_the_artifacts(self) -> None:
        setup = self.setup_with(INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE, *CHAPTER_TWO, AUDIT, SCORE, PACKAGE)
        view = RecordingView(answers=["", "", ""])

        result = run_session(self.project, setup, view)

        self.assertEqual("completed", result.status, msg=view.calls)
        titles = [title for title, _, _ in view.checkpoints]
        self.assertEqual(["The brief", "The outline", "Chapter 1, read blind"], titles)
        self.assertIn("BRIEF-SENTINEL", view.checkpoints[0][1])
        self.assertIn("## Chapter 2: The Drive", view.checkpoints[1][1])
        # The panel carries the title, so the artifact's own H1 is not repeated inside it.
        self.assertNotIn("# Brief", view.checkpoints[0][1])
        self.assertNotIn("# Outline", view.checkpoints[1][1])
        chapter_body = view.checkpoints[2][1]
        self.assertNotIn("# Chapter 1: The Watch Room", chapter_body)
        self.assertIn("3 of 3 blind readers would turn the page", chapter_body)
        self.assertIn("the hum", chapter_body)  # what they remembered
        self.assertIn("DISRUPTED-SENTINEL", chapter_body)  # the opening of the prose itself
        self.assertIn("Enter", view.checkpoints[2][2])

    def test_notes_at_the_brief_rerun_intake_with_them(self) -> None:
        setup = self.setup_with(INTAKE, INTAKE_DARKER, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE, *CHAPTER_TWO, AUDIT, SCORE, PACKAGE)
        view = RecordingView(answers=["make it darker, less cosy", "", "", ""])

        result = run_session(self.project, setup, view)

        self.assertEqual("completed", result.status, msg=view.calls)
        self.assertEqual(4, len(view.checkpoints))
        self.assertIn("BRIEF-SENTINEL", view.checkpoints[0][1])
        self.assertIn("BRIEF-DARKER", view.checkpoints[1][1])  # shown again after the rerun
        notes = (self.project / "work" / "author-notes.md").read_text(encoding="utf-8")
        self.assertIn("make it darker", notes)
        prompts = [call.prompt for call in setup.adapters["architect"].calls]
        self.assertNotIn("make it darker", prompts[0])
        self.assertIn("make it darker, less cosy", prompts[1])  # the rerun saw the notes
        self.assertIn("Author notes", prompts[2])  # and so does every later phase
        self.assertIn("(rewritten with your notes)", [call[2] for call in view.calls if call[0] == "done"][1])

    def test_q_at_the_outline_stops_before_any_prose_and_says_how_to_resume(self) -> None:
        setup = self.setup_with(INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE)
        view = RecordingView(answers=["", "q"])

        result = run_session(self.project, setup, view)

        self.assertEqual("stopped", result.status)
        self.assertIn("book-genesis resume", result.message)
        self.assertFalse((self.project / "manuscript" / "chapters").exists() and any((self.project / "manuscript" / "chapters").iterdir()))
        self.assertEqual(["Architecture"], view.stages("stop"))
        self.assertEqual(3, len(setup.adapters["writer"].calls))  # intake, foundation, architecture; no writer call

    def test_notes_at_chapter_one_rewrite_it_and_reach_chapter_two(self) -> None:
        rewritten = DRAFT.replace("DRAFT-SENTINEL", "REWRITTEN-SENTINEL")
        setup = self.setup_with(
            INTAKE, FOUNDATION, ARCHITECTURE,
            *CHAPTER_ONE,
            rewritten, rewritten, YES, YES, YES,  # chapter 1 again with the notes (writer, disruptor, panel)
            *CHAPTER_TWO, AUDIT, SCORE, PACKAGE,
        )
        view = RecordingView(answers=["", "", "open on the body, not the dashboards", ""])

        result = run_session(self.project, setup, view)

        self.assertEqual("completed", result.status, msg=view.calls)
        self.assertEqual(4, len(view.checkpoints))
        self.assertIn("REWRITTEN-SENTINEL", view.checkpoints[3][1])
        chapter_one = (self.project / "manuscript" / "chapters" / "chapter-01.md").read_text(encoding="utf-8")
        self.assertIn("REWRITTEN-SENTINEL", chapter_one)
        writer_prompts = [call.prompt for call in setup.adapters["writer"].calls]
        rewrite_prompt = writer_prompts[3 + 5]  # 3 phases + 5 calls of the first chapter 1 pass
        self.assertIn("open on the body, not the dashboards", rewrite_prompt)
        chapter_two_brief = (self.project / "briefs" / "chapter-02.md").read_text(encoding="utf-8")
        self.assertIn("open on the body", chapter_two_brief)
        self.assertEqual(10.0, view.card.score)  # the rerun is what counts, not the first pass

    def test_a_reader_who_stops_costs_score_and_a_blocked_chapter_ends_the_run(self) -> None:
        # Chapter 1: panel 2 of 3 turn the page (accepted, cycles 0). Chapter 2: judge says no
        # twice; the thriller profile allows a limited number of cycles, then the chapter blocks.
        responses = [INTAKE, FOUNDATION, ARCHITECTURE, DRAFT, DISRUPTED, YES, NO, YES, DRAFT, DISRUPTED] + [NO, DRAFT] * 6
        setup = self.setup_with(*responses)
        view = RecordingView()

        result = run_session(self.project, setup, view, yes=True)

        self.assertEqual("blocked", result.status, msg=view.calls)
        self.assertEqual(["Drafting"], view.stages("fail"))
        self.assertIsNone(view.card)  # no score for an unfinished book

    def test_chapter_cap_stops_after_the_requested_chapters(self) -> None:
        setup = self.setup_with(INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE)
        view = RecordingView()

        result = run_session(self.project, setup, view, yes=True, chapters=1)

        self.assertEqual("stopped", result.status, msg=view.calls)
        self.assertIn("stopped after 1 of 2 chapters", result.message)
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-01.md").exists())
        self.assertFalse((self.project / "manuscript" / "chapters" / "chapter-02.md").exists())


class StripHeadingTests(unittest.TestCase):
    def test_only_the_artifacts_own_title_goes_and_nothing_else(self) -> None:
        self.assertEqual("BRIEF", strip_leading_heading("# Brief\n\nBRIEF"))
        self.assertEqual("## Chapter 1\n\nprose", strip_leading_heading("# Outline\n\n## Chapter 1\n\nprose"))
        self.assertEqual("prose\n\n# Later heading", strip_leading_heading("prose\n\n# Later heading"))
        self.assertEqual("", strip_leading_heading(""))


class InterpretTests(unittest.TestCase):
    def test_enter_and_yes_continue_q_stops_anything_else_is_a_note(self) -> None:
        self.assertEqual(("continue", ""), interpret(""))
        self.assertEqual(("continue", ""), interpret("  YES "))
        self.assertEqual(("continue", ""), interpret("sim"))
        self.assertEqual(("stop", ""), interpret("q"))
        self.assertEqual(("stop", ""), interpret("não"))
        self.assertEqual(("notes", "less exposition in chapter 1"), interpret("less exposition in chapter 1"))


if __name__ == "__main__":
    unittest.main()
