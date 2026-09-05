"""What the guided session actually draws (ADR 0009).

Rendered through a rich Console with a fixed width and no colour, so the assertions are about
layout and wording, not escape codes.
"""
from pathlib import Path
import io
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.score import Component, ScoreCard  # type: ignore  # noqa: E402
from runner.ui import PlainView, RichView, make_view  # type: ignore  # noqa: E402

CARD = ScoreCard(
    8.4,
    3,
    [
        Component("panel", "Reader panel", 1.0, "3 of 3 blind readers would turn the page", 0.4),
        Component("first_pass", "First-draft acceptance", 0.66, "2 of 3 chapters accepted on the first draft", 0.3),
        Component("accepted", "Chapters accepted", 1.0, "3 of 3 chapters accepted in the end", 0.2),
        Component("remembered", "Memorable", 0.33, "1 of 3 chapters left the reader with something specific", 0.1),
    ],
    [],
)


def rendered(build) -> str:
    from rich.console import Console

    buffer = io.StringIO()
    console = Console(file=buffer, width=100, no_color=True, force_terminal=False, legacy_windows=False)
    view = RichView(interactive=False, live=False, console=console)
    build(view)
    return buffer.getvalue()


class RichViewTests(unittest.TestCase):
    def test_the_header_names_the_book_and_who_writes_and_judges(self) -> None:
        text = rendered(
            lambda view: view.header(
                title="The Watch Room",
                idea="a night-shift analyst in Brussels",
                language="en",
                roles={"writer": "claude claude-opus-5", "judge": "codex gpt-5.5"},
                warnings=["single family: writer and judge both run on `claude`"],
            )
        )
        self.assertIn("B O O K   G E N E S I S", text)
        self.assertIn("The Watch Room", text)
        self.assertIn("a night-shift analyst in Brussels", text)
        self.assertIn("claude claude-opus-5", text)
        self.assertIn("codex gpt-5.5", text)
        self.assertIn("single family", text)

    def test_the_stage_track_shows_every_stage_with_the_active_one_marked(self) -> None:
        def build(view: RichView) -> None:
            view.stage_done("Intake", "The Watch Room, thriller")
            view.stage_start("Foundation")
            view.event("chapter 1: writer (claude claude-opus-5)...")
            view.checkpoint("anything", "body", "hint")  # prints the track as it stands now

        text = rendered(build)
        for stage in ("Intake", "Foundation", "Architecture", "Drafting", "Audit", "Score", "Package"):
            self.assertIn(stage, text)
        self.assertIn("The Watch Room", text)
        self.assertIn("✔", text)  # Intake is done
        self.assertIn(">", text)  # Foundation is running, without the live spinner
        self.assertIn("chapter 1: writer", text)  # the pipeline events under the track

    def test_a_checkpoint_shows_the_artifact_and_the_three_choices(self) -> None:
        # The choices belong in the frame: on a long outline the input prompt scrolls away.
        text = rendered(lambda view: view.checkpoint("The outline", "## Chapter 1: The Watch Room\n\nHalden watches.", "Enter = go on  |  type what to change  |  q = stop here"))
        self.assertIn("The outline", text)
        self.assertIn("Chapter 1: The Watch Room", text)
        self.assertIn("Enter = go on", text)
        self.assertIn("q = stop here", text)

    def test_the_score_panel_shows_every_component_and_where_the_number_came_from(self) -> None:
        text = rendered(lambda view: view.score(CARD))
        self.assertIn("Genesis Score", text)
        self.assertIn("8.4", text)
        self.assertIn("readers kept going", text)
        self.assertIn("3 of 3 blind readers would turn the page", text)
        self.assertIn("40%", text)
        self.assertIn("receive prose without the outline", text)

    def test_a_failure_is_red_and_says_what_happened(self) -> None:
        text = rendered(lambda view: view.stage_fail("Drafting", "chapter 2 blocked after 3 revision cycles"))
        self.assertIn("chapter 2 blocked", text)


class PlainViewTests(unittest.TestCase):
    def render(self, build) -> str:
        buffer = io.StringIO()
        view = PlainView(interactive=False, out=buffer)
        build(view)
        return buffer.getvalue()

    def test_plain_view_prints_the_same_facts_as_lines(self) -> None:
        def build(view: PlainView) -> None:
            view.header(title="The Watch Room", idea="an analyst", language="en", roles={"writer": "claude opus"}, warnings=[])
            view.stage_start("Intake")
            view.stage_done("Intake", "thriller")
            view.score(CARD)
            view.finish({"manuscript": Path("books/x/manuscript/chapters")})

        text = self.render(build)
        self.assertIn("BOOK GENESIS", text)
        self.assertIn("The Watch Room", text)
        self.assertIn("writer: claude opus", text)
        self.assertIn("Intake: running", text)
        self.assertIn("Intake: done", text)
        self.assertIn("8.4 / 10", text)
        self.assertIn("manuscript: books", text)

    def test_a_checkpoint_without_a_terminal_never_blocks(self) -> None:
        text = self.render(lambda view: view.checkpoint("The brief", "BRIEF", "hint"))
        self.assertIn("The brief", text)
        self.assertIn("BRIEF", text)


class Cp1252Stream(io.StringIO):
    """A Windows console on the default code page: writing a box-drawing character raises,
    exactly as the real one did on 2026-09-04."""

    encoding = "cp1252"

    def write(self, text: str) -> int:
        text.encode("cp1252")  # raises UnicodeEncodeError on anything cp1252 cannot carry
        return super().write(text)


class LegacyConsoleTests(unittest.TestCase):
    """Regression: rich's rounded panels crashed the whole run with UnicodeEncodeError on a
    cp1252 console. A Windows vibecoder must never see a traceback instead of a book."""

    def render_on_cp1252(self, build) -> str:
        from rich.console import Console

        stream = Cp1252Stream()
        console = Console(file=stream, width=100, no_color=True, force_terminal=False, legacy_windows=False)
        view = RichView(interactive=False, live=False, console=console)
        self.assertFalse(view.unicode)
        build(view)
        return stream.getvalue()

    def test_the_whole_session_draws_in_ascii_without_crashing(self) -> None:
        def build(view: RichView) -> None:
            view.header(title="The Watch Room", idea="an analyst", language="en", roles={"writer": "claude opus"}, warnings=[])
            view.stage_done("Intake", "The Watch Room, thriller")
            view.stage_start("Foundation")
            view.checkpoint("The brief", "# Brief\n\nBRIEF-SENTINEL", "Enter = go on")
            view.score(CARD)
            view.finish({"manuscript": Path("books/x")})

        text = self.render_on_cp1252(build)
        self.assertIn("B O O K   G E N E S I S", text)
        self.assertIn("BRIEF-SENTINEL", text)
        self.assertIn("8.4", text)
        self.assertIn("+", text)  # ASCII panel corners
        for forbidden in ("─", "╭", "║", "✔", "○"):
            self.assertNotIn(forbidden, text)

    def test_unicode_stream_keeps_the_prettier_glyphs(self) -> None:
        text = rendered(lambda view: view.stage_done("Intake", "done"))
        self.assertIn("✔", text)

    def test_a_finished_stage_without_live_prints_one_line_not_the_whole_track(self) -> None:
        # Bug found 2026-09-04: every finished stage reprinted all seven stages, so a piped
        # run stacked seven copies of the track down the log.
        def build(view: RichView) -> None:
            view.stage_done("Intake", "MARKER-INTAKE")
            view.stage_done("Foundation", "MARKER-FOUNDATION")

        text = rendered(build)
        self.assertEqual(1, text.count("MARKER-INTAKE"))
        self.assertEqual(1, text.count("MARKER-FOUNDATION"))
        self.assertEqual(0, text.count("Architecture"))  # stages still to come are not reprinted

    def test_the_track_is_printed_once_before_a_checkpoint(self) -> None:
        def build(view: RichView) -> None:
            view.stage_start("Foundation")
            view.checkpoint("The brief", "body", "hint")
            view.checkpoint("Again", "body", "hint")

        text = rendered(build)
        self.assertEqual(1, text.count("Architecture"))  # one track, not one per checkpoint

    def test_an_artifacts_own_h1_is_not_drawn_as_a_box_inside_the_panel(self) -> None:
        text = rendered(lambda view: view.checkpoint("The brief", "# Brief\n\nBRIEF-SENTINEL", "hint"))
        self.assertIn("The brief", text)  # the panel title carries it
        self.assertIn("BRIEF-SENTINEL", text)
        self.assertEqual(0, text.count("Brief\n"))  # the duplicated H1 is gone
        self.assertNotIn("┏", text)  # and so is the heavy box rich draws around an H1

    def test_a_body_that_does_not_start_with_a_heading_is_untouched(self) -> None:
        text = rendered(lambda view: view.checkpoint("Chapter 1, read blind", "**3 of 3 would turn the page.**\n\n# Chapter 1\n\nprose", "hint"))
        self.assertIn("3 of 3 would turn the page", text)
        self.assertIn("Chapter 1", text)
        self.assertIn("prose", text)

    def test_brackets_in_a_message_are_not_read_as_style_tags(self) -> None:
        text = rendered(lambda view: view.fail("stopped: flags=[exposition] in C:\\books\\[draft]"))
        self.assertIn("flags=[exposition]", text)
        self.assertIn("[draft]", text)


class MakeViewTests(unittest.TestCase):
    def test_plain_is_requested_explicitly_and_rich_is_the_default(self) -> None:
        self.assertIsInstance(make_view(plain=True, interactive=False), PlainView)
        self.assertIsInstance(make_view(plain=False, interactive=False), RichView)

    def test_the_view_knows_whether_it_can_ask_anything(self) -> None:
        self.assertFalse(make_view(plain=True, interactive=False).interactive)
        self.assertTrue(make_view(plain=True, interactive=True).interactive)


if __name__ == "__main__":
    unittest.main()
