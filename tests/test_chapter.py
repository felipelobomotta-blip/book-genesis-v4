from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import FakeAdapter  # type: ignore  # noqa: E402
from runner.chapter import AwaitingHuman, approve, run_chapter  # type: ignore  # noqa: E402
from runner.filesystem import scaffold_project  # type: ignore  # noqa: E402


OUTLINE = """# Outline

## Chapter 1: The Watch Room

OUTLINE-SENTINEL-CH1 Halden watches the dashboards and laughs.

## Chapter 2: The Drive

OUTLINE-SENTINEL-CH2 Halden drives Yusuf south.
"""

DRAFT = "# Chapter 1: The Watch Room\n\nDRAFT-SENTINEL Halden counted the hum. " + ("The console blinked. " * 20) + "\n"
DISRUPTED = DRAFT.replace("DRAFT-SENTINEL", "DISRUPTED-SENTINEL")
EDITED = DRAFT.replace("DRAFT-SENTINEL", "EDITED-SENTINEL")
EDITED_AGAIN = DRAFT.replace("DRAFT-SENTINEL", "EDITED-AGAIN-SENTINEL")

YES = (
    "```yaml\nturn_page: yes\nstopped_at: none\nremember:\n  - the hum\nflags: []\n"
    "vs_previous: none\nvs_anchor: none\n```\n"
)
YES_BETTER = YES.replace("vs_previous: none", "vs_previous: better")
YES_WORSE = YES.replace("vs_previous: none", "vs_previous: worse")
NO_HOOK = (
    '```yaml\nturn_page: no\nstopped_at: "The console blinked."\nremember: []\nflags: [hook]\n'
    "vs_previous: none\nvs_anchor: none\n```\n"
)


def make_project(genre: str = "thriller") -> Path:
    project = Path(tempfile.mkdtemp(prefix="book-genesis-chapter-"))
    scaffold_project(project, idea="collapse fiction", adapter="fake", model_name="fake", language="en")
    state = project / "PROJECT_STATE.yaml"
    state.write_text(state.read_text(encoding="utf-8").replace('genre: ""', f'genre: "{genre}"'), encoding="utf-8")
    (project / "artifacts" / "05-outline.md").write_text(OUTLINE, encoding="utf-8")
    (project / "artifacts" / "02-story-engine.md").write_text("# Story Engine\n\nENGINE-SENTINEL\n", encoding="utf-8")
    (project / "artifacts" / "03-characters.md").write_text("# Characters\n\nCHARACTERS-SENTINEL\n", encoding="utf-8")
    return project


def make_adapters(writer=(), disruptor=(), judge=(), editor=()):
    return {
        "writer": FakeAdapter(writer),
        "disruptor": FakeAdapter(disruptor),
        "judge": FakeAdapter(judge),
        "editor": FakeAdapter(editor),
    }


class RunChapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = make_project()

    def tearDown(self) -> None:
        shutil.rmtree(self.project, ignore_errors=True)

    def chapter_file(self, number: int = 1) -> Path:
        return self.project / "manuscript" / "chapters" / f"chapter-{number:02d}.md"

    def test_writer_sees_the_brief_and_the_judge_never_sees_the_plan(self) -> None:
        adapters = make_adapters(writer=[DRAFT], disruptor=[DISRUPTED], judge=[YES])
        result = run_chapter(self.project, 1, adapters)

        self.assertIn("OUTLINE-SENTINEL-CH1", adapters["writer"].calls[0].prompt)
        judge_prompt = adapters["judge"].calls[0].prompt
        self.assertNotIn("OUTLINE-SENTINEL-CH1", judge_prompt)
        self.assertNotIn("CHARACTERS-SENTINEL", judge_prompt)
        self.assertNotIn("ENGINE-SENTINEL", judge_prompt)
        self.assertIn("DISRUPTED-SENTINEL", judge_prompt)

        self.assertTrue(result.accepted)
        self.assertIn("DISRUPTED-SENTINEL", self.chapter_file().read_text(encoding="utf-8"))
        self.assertTrue((self.project / "manuscript" / "drafts" / "chapter-01" / "draft-1.md").exists())
        self.assertTrue((self.project / "evaluations" / "chapter-01-judge-1.md").exists())

    def test_editor_runs_only_when_the_reader_stops(self) -> None:
        adapters = make_adapters(writer=[DRAFT], disruptor=[DISRUPTED], judge=[NO_HOOK, YES_BETTER], editor=[EDITED])
        result = run_chapter(self.project, 1, adapters)

        self.assertEqual(1, len(adapters["editor"].calls))
        editor_prompt = adapters["editor"].calls[0].prompt
        self.assertIn("hook", editor_prompt)
        self.assertIn("The console blinked.", editor_prompt)
        self.assertIn("DISRUPTED-SENTINEL", editor_prompt)

        second_judge_prompt = adapters["judge"].calls[1].prompt
        self.assertIn("EDITED-SENTINEL", second_judge_prompt)
        self.assertIn("DISRUPTED-SENTINEL", second_judge_prompt)

        self.assertTrue(result.accepted)
        self.assertIn("EDITED-SENTINEL", self.chapter_file().read_text(encoding="utf-8"))
        self.assertTrue((self.project / "manuscript" / "drafts" / "chapter-01" / "draft-2.md").exists())

    def test_a_worse_edit_is_discarded_and_the_next_edit_starts_from_the_best_draft(self) -> None:
        adapters = make_adapters(
            writer=[DRAFT],
            disruptor=[DISRUPTED],
            judge=[NO_HOOK, YES_WORSE, YES_BETTER],
            editor=[EDITED, EDITED_AGAIN],
        )
        result = run_chapter(self.project, 1, adapters)

        second_editor_prompt = adapters["editor"].calls[1].prompt
        self.assertIn("DISRUPTED-SENTINEL", second_editor_prompt)
        self.assertNotIn("EDITED-SENTINEL Halden", second_editor_prompt)
        self.assertTrue(result.accepted)
        self.assertIn("EDITED-AGAIN-SENTINEL", self.chapter_file().read_text(encoding="utf-8"))

    def test_loop_stops_after_max_cycles_without_accepting(self) -> None:
        adapters = make_adapters(
            writer=[DRAFT],
            disruptor=[DISRUPTED],
            judge=[NO_HOOK, NO_HOOK, NO_HOOK, NO_HOOK],
            editor=[EDITED, EDITED, EDITED],
        )
        result = run_chapter(self.project, 1, adapters)

        self.assertFalse(result.accepted)
        self.assertEqual("blocked", result.status)
        self.assertEqual(3, len(adapters["editor"].calls))
        self.assertFalse(self.chapter_file().exists())

    def test_nonfiction_skips_the_disruptor(self) -> None:
        shutil.rmtree(self.project, ignore_errors=True)
        self.project = make_project(genre="nonfiction")
        adapters = make_adapters(writer=[DRAFT], judge=[YES])
        result = run_chapter(self.project, 1, adapters)

        self.assertEqual([], adapters["disruptor"].calls)
        self.assertTrue(result.accepted)
        self.assertIn("DRAFT-SENTINEL", self.chapter_file().read_text(encoding="utf-8"))

    def test_craft_notes_never_reach_the_manuscript_or_the_next_pass(self) -> None:
        noisy = DRAFT + "\n\n## Craft notes\n\nNOTES-SENTINEL I withheld the dog on purpose.\n"
        adapters = make_adapters(writer=[noisy], disruptor=[DISRUPTED], judge=[YES])
        run_chapter(self.project, 1, adapters)

        self.assertNotIn("NOTES-SENTINEL", adapters["disruptor"].calls[0].prompt)
        self.assertNotIn("NOTES-SENTINEL", (self.project / "manuscript" / "drafts" / "chapter-01" / "draft-1.md").read_text(encoding="utf-8"))

    def test_second_chapter_waits_for_a_human_to_read_the_first(self) -> None:
        run_chapter(self.project, 1, make_adapters(writer=[DRAFT], disruptor=[DISRUPTED], judge=[YES]))

        with self.assertRaises(AwaitingHuman):
            run_chapter(self.project, 2, make_adapters(writer=[DRAFT], disruptor=[DISRUPTED], judge=[YES]))

        approve(self.project, "chapter-01")
        adapters = make_adapters(writer=[DRAFT], disruptor=[DISRUPTED], judge=[YES])
        result = run_chapter(self.project, 2, adapters)
        self.assertTrue(result.accepted)
        self.assertIn("OUTLINE-SENTINEL-CH2", adapters["writer"].calls[0].prompt)
        self.assertIn("DISRUPTED-SENTINEL", adapters["judge"].calls[0].prompt)


if __name__ == "__main__":
    unittest.main()
