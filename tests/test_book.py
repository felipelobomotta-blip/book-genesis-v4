from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import FakeAdapter  # type: ignore  # noqa: E402
from runner.book import count_chapters, run_book  # type: ignore  # noqa: E402
from runner.chapter import approve  # type: ignore  # noqa: E402
from runner.filesystem import scaffold_project  # type: ignore  # noqa: E402


OUTLINE = """# Outline

## Macro structure

Two chapters for the test.

## Chapter 1: The Watch Room

OUTLINE-SENTINEL-CH1 Halden watches the dashboards and laughs.

## Chapter 2: The Drive

OUTLINE-SENTINEL-CH2 Halden drives Yusuf south.

## Tension map

Rising.
"""
DRAFT = "# Chapter 1: The Watch Room\n\nDRAFT-SENTINEL Halden counted the hum. " + ("The console blinked. " * 20) + "\n"
DISRUPTED = DRAFT.replace("DRAFT-SENTINEL", "DISRUPTED-SENTINEL")
YES = (
    "```yaml\nturn_page: yes\nstopped_at: none\nremember:\n  - the hum\nflags: []\n"
    "vs_previous: none\nvs_anchor: none\n```\n"
)


def make_project() -> Path:
    project = Path(tempfile.mkdtemp(prefix="book-genesis-book-"))
    scaffold_project(project, idea="collapse fiction", adapter="fake", model_name="fake", language="en")
    state = project / "PROJECT_STATE.yaml"
    state.write_text(state.read_text(encoding="utf-8").replace('genre: ""', 'genre: "thriller"'), encoding="utf-8")
    (project / "artifacts" / "05-outline.md").write_text(OUTLINE, encoding="utf-8")
    (project / "artifacts" / "02-story-engine.md").write_text("# Story Engine\n\nENGINE-SENTINEL\n", encoding="utf-8")
    (project / "artifacts" / "03-characters.md").write_text("# Characters\n\nCHARACTERS-SENTINEL\n", encoding="utf-8")
    return project


def shared_adapters(responses):
    adapter = FakeAdapter(responses)
    return {role: adapter for role in ("writer", "disruptor", "judge", "editor")}, {}


class CountChaptersTests(unittest.TestCase):
    def test_counts_chapter_headings_only(self) -> None:
        self.assertEqual(2, count_chapters(OUTLINE))

    def test_no_chapters_is_zero(self) -> None:
        self.assertEqual(0, count_chapters("# Outline\n\n## Macro structure\n\nNothing yet.\n"))

    def test_counts_bold_portuguese_markers_too(self) -> None:
        outline = (
            "## Outline por capítulo\n\n**Capítulo 1 — A**\n\ntexto\n\n**Capítulo 2 — B**\n\n"
            "### PARTE II\n\n**Capítulo 38 — Z**\n\n## Mapa de tensão\n"
        )
        self.assertEqual(38, count_chapters(outline))


class RunBookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = make_project()

    def tearDown(self) -> None:
        shutil.rmtree(self.project, ignore_errors=True)

    def chapter_file(self, number: int) -> Path:
        return self.project / "manuscript" / "chapters" / f"chapter-{number:02d}.md"

    def test_writes_the_whole_book_without_a_human_by_default(self) -> None:
        adapters, models = shared_adapters([DRAFT, DISRUPTED, YES, DRAFT, DISRUPTED, YES])
        result = run_book(self.project, adapters, models)

        self.assertEqual("completed", result.status)
        self.assertEqual([1, 2], result.chapters_done)
        self.assertTrue(self.chapter_file(1).exists())
        self.assertTrue(self.chapter_file(2).exists())

    def test_human_mode_stops_after_chapter_one_until_approved(self) -> None:
        adapters, models = shared_adapters([DRAFT, DISRUPTED, YES, DRAFT, DISRUPTED, YES])
        result = run_book(self.project, adapters, models, human_checkpoint=True)

        self.assertEqual("awaiting_human", result.status)
        self.assertEqual([1], result.chapters_done)
        self.assertFalse(self.chapter_file(2).exists())

        approve(self.project, "chapter-01")
        result = run_book(self.project, adapters, models, human_checkpoint=True)
        self.assertEqual("completed", result.status)
        self.assertEqual([2], result.chapters_done)

    def test_chapter_one_is_judged_by_the_panel_when_one_is_given(self) -> None:
        from runner.panel import PanelJudge, PanelMember

        member_adapters = [FakeAdapter([YES]) for _ in range(3)]
        panel = PanelJudge(
            [
                PanelMember(adapter=adapter, model="", persona=f"persona {index}")
                for index, adapter in enumerate(member_adapters)
            ]
        )
        adapters, models = shared_adapters([DRAFT, DISRUPTED, DRAFT, DISRUPTED, YES])
        result = run_book(self.project, adapters, models, panel=panel)

        self.assertEqual("completed", result.status)
        self.assertEqual(3, sum(len(adapter.calls) for adapter in member_adapters))
        self.assertIn("DISRUPTED-SENTINEL", member_adapters[0].calls[0].prompt)

    def test_existing_chapters_are_skipped(self) -> None:
        approve(self.project, "chapter-01")
        self.chapter_file(1).write_text("# Chapter 1\n\nAlready written by hand.\n", encoding="utf-8")
        adapters, models = shared_adapters([DRAFT, DISRUPTED, YES])
        result = run_book(self.project, adapters, models)

        self.assertEqual("completed", result.status)
        self.assertEqual([2], result.chapters_done)
        self.assertIn("OUTLINE-SENTINEL-CH2", adapters["writer"].calls[0].prompt)
        self.assertIn("Already written by hand.", self.chapter_file(1).read_text(encoding="utf-8"))

    def test_a_blocked_chapter_stops_the_book(self) -> None:
        approve(self.project, "chapter-01")
        no = YES.replace("turn_page: yes", "turn_page: no").replace("flags: []", "flags: [pacing]")
        adapters, models = shared_adapters([DRAFT, DISRUPTED, no, DRAFT, no, DRAFT, no, DRAFT, no])
        result = run_book(self.project, adapters, models)

        self.assertEqual("blocked", result.status)
        self.assertEqual([], result.chapters_done)
        self.assertEqual(1, result.last_chapter)


if __name__ == "__main__":
    unittest.main()
