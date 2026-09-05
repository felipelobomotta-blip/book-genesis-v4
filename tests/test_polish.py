from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import FakeAdapter  # type: ignore  # noqa: E402
from runner.book import run_polish  # type: ignore  # noqa: E402
from runner.chapter import run_chapter  # type: ignore  # noqa: E402
from runner.filesystem import scaffold_project  # type: ignore  # noqa: E402


EXISTING = (
    "# Chapter 1: The Watch Room\n\n"
    "EXISTING-SENTINEL Halden counted the hum. " + ("The console blinked. " * 20) + "\n"
)
EDITED = EXISTING.replace("EXISTING-SENTINEL", "EDITED-SENTINEL")
EDITED_WORSE = EXISTING.replace("EXISTING-SENTINEL", "EDITED-WORSE-SENTINEL")

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
YES_FLAGGED = (
    "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: [ai_pattern]\n"
    "vs_previous: none\nvs_anchor: none\n```\n"
)


def make_project(genre: str = "thriller") -> Path:
    project = Path(tempfile.mkdtemp(prefix="book-genesis-polish-"))
    scaffold_project(project, idea="collapse fiction", adapter="fake", model_name="fake", language="en")
    state = project / "PROJECT_STATE.yaml"
    state.write_text(state.read_text(encoding="utf-8").replace('genre: ""', f'genre: "{genre}"'), encoding="utf-8")
    return project


def seed_chapter(project: Path, number: int = 1, text: str = EXISTING) -> Path:
    chapters = project / "manuscript" / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    path = chapters / f"chapter-{number:02d}.md"
    path.write_text(text, encoding="utf-8")
    return path


def make_adapters(writer=(), disruptor=(), judge=(), editor=()):
    return {
        "writer": FakeAdapter(writer),
        "disruptor": FakeAdapter(disruptor),
        "judge": FakeAdapter(judge),
        "editor": FakeAdapter(editor),
    }


class PolishChapterTests(unittest.TestCase):
    def test_seed_skips_writer_and_disruptor_and_keeps_original_in_drafts(self):
        project = make_project()
        path = seed_chapter(project)
        adapters = make_adapters(judge=[YES])
        result = run_chapter(project, 1, adapters, seed_draft=EXISTING)
        self.assertTrue(result.accepted)
        self.assertEqual(result.cycles, 0)
        self.assertEqual(adapters["writer"].calls, [])
        self.assertEqual(adapters["disruptor"].calls, [])
        self.assertEqual(len(adapters["judge"].calls), 1)
        self.assertEqual(len(adapters["editor"].calls), 0)
        final = path.read_text(encoding="utf-8")
        self.assertIn("EXISTING-SENTINEL", final)
        draft1 = (project / "manuscript" / "drafts" / "chapter-01" / "draft-1.md").read_text(encoding="utf-8")
        self.assertIn("EXISTING-SENTINEL", draft1)

    def test_flagged_seed_is_revised_by_editor_and_approved(self):
        project = make_project()
        path = seed_chapter(project)
        adapters = make_adapters(judge=[NO_HOOK, YES_BETTER], editor=[EDITED])
        result = run_chapter(project, 1, adapters, seed_draft=EXISTING)
        self.assertTrue(result.accepted)
        self.assertEqual(result.cycles, 1)
        self.assertEqual(len(adapters["editor"].calls), 1)
        final = path.read_text(encoding="utf-8")
        self.assertIn("EDITED-SENTINEL", final)
        draft2 = (project / "manuscript" / "drafts" / "chapter-01" / "draft-2.md").read_text(encoding="utf-8")
        self.assertIn("EDITED-SENTINEL", draft2)

    def test_budget_spent_without_approval_leaves_chapter_untouched(self):
        project = make_project()
        path = seed_chapter(project)
        adapters = make_adapters(judge=[NO_HOOK, YES_WORSE, YES_WORSE, YES_WORSE], editor=[EDITED_WORSE, EDITED_WORSE, EDITED_WORSE])
        result = run_chapter(project, 1, adapters, seed_draft=EXISTING)
        self.assertFalse(result.accepted)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.cycles, 3)
        final = path.read_text(encoding="utf-8")
        self.assertIn("EXISTING-SENTINEL", final)
        self.assertNotIn("EDITED-WORSE-SENTINEL", final)

    def test_flagged_accepted_seed_gets_editor_pass(self):
        project = make_project()
        path = seed_chapter(project)
        adapters = make_adapters(judge=[YES_FLAGGED, YES_BETTER], editor=[EDITED])
        result = run_chapter(project, 1, adapters, seed_draft=EXISTING, revise_on_flags=True)
        self.assertTrue(result.accepted)
        self.assertEqual(result.cycles, 1)
        self.assertEqual(len(adapters["editor"].calls), 1)
        final = path.read_text(encoding="utf-8")
        self.assertIn("EDITED-SENTINEL", final)

    def test_flagged_accepted_seed_without_revise_on_flags_stays_untouched(self):
        project = make_project()
        path = seed_chapter(project)
        adapters = make_adapters(judge=[YES_FLAGGED], editor=[EDITED])
        result = run_chapter(project, 1, adapters, seed_draft=EXISTING)
        self.assertTrue(result.accepted)
        self.assertEqual(result.cycles, 0)
        self.assertEqual(adapters["editor"].calls, [])
        final = path.read_text(encoding="utf-8")
        self.assertIn("EXISTING-SENTINEL", final)

    def test_run_polish_revises_on_flags_by_default(self):
        project = make_project()
        seed_chapter(project, 1)
        adapters = make_adapters(judge=[YES_FLAGGED, YES_BETTER], editor=[EDITED])
        result = run_polish(project, adapters, {}, start=1, end=1)
        self.assertEqual(result.status, "polished")
        self.assertEqual(len(adapters["editor"].calls), 1)
        final = (project / "manuscript" / "chapters" / "chapter-01.md").read_text(encoding="utf-8")
        self.assertIn("EDITED-SENTINEL", final)


class RunPolishTests(unittest.TestCase):
    def test_reads_existing_files_and_reports_missing(self):
        project = make_project()
        seed_chapter(project, 1)
        seed_chapter(project, 3)
        adapters = make_adapters(judge=[YES, YES])
        messages = []
        result = run_polish(project, adapters, {}, start=1, end=3, progress=messages.append)
        self.assertEqual(result.status, "polished")
        self.assertEqual(result.chapters_done, [1, 3])
        self.assertIn("2", result.message)
        self.assertEqual(len(adapters["judge"].calls), 2)
        self.assertEqual(adapters["writer"].calls, [])
        self.assertTrue(any("chapter 2" in message for message in messages))

    def test_blocked_run_stops_and_reports(self):
        project = make_project()
        seed_chapter(project, 1)
        seed_chapter(project, 2)
        adapters = make_adapters(judge=[NO_HOOK, YES_WORSE, YES_WORSE, YES_WORSE], editor=[EDITED_WORSE, EDITED_WORSE, EDITED_WORSE])
        result = run_polish(project, adapters, {}, start=1, end=2)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.chapters_done, [])
        self.assertEqual(result.last_chapter, 1)

    def test_no_chapters_raises(self):
        project = make_project()
        adapters = make_adapters(judge=[YES])
        with self.assertRaises(ValueError):
            run_polish(project, adapters, {})


if __name__ == "__main__":
    unittest.main()
