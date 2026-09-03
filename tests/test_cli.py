from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.filesystem import scaffold_project  # type: ignore  # noqa: E402


OUTLINE = """# Outline

## Chapter 1: The Watch Room

OUTLINE-SENTINEL-CH1 Halden watches the dashboards and laughs.

## Chapter 2: The Drive

OUTLINE-SENTINEL-CH2 Halden drives Yusuf south.
"""
DRAFT = "# Chapter 1: The Watch Room\n\nDRAFT-SENTINEL Halden counted the hum. " + ("The console blinked. " * 20) + "\n"
DISRUPTED = DRAFT.replace("DRAFT-SENTINEL", "DISRUPTED-SENTINEL")
YES = (
    "```yaml\nturn_page: yes\nstopped_at: none\nremember:\n  - the hum\nflags: []\n"
    "vs_previous: none\nvs_anchor: none\n```\n"
)
SEPARATOR = "\n=== NEXT ===\n"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "runner" / "cli.py"), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-cli-"))
        self.project = self.tempdir / "project"
        scaffold_project(self.project, idea="collapse fiction", adapter="fake", model_name="fake", language="en")
        state = self.project / "PROJECT_STATE.yaml"
        state.write_text(state.read_text(encoding="utf-8").replace('genre: ""', 'genre: "thriller"'), encoding="utf-8")
        (self.project / "artifacts" / "05-outline.md").write_text(OUTLINE, encoding="utf-8")
        (self.project / "artifacts" / "02-story-engine.md").write_text("# Story Engine\n\nENGINE-SENTINEL\n", encoding="utf-8")
        (self.project / "artifacts" / "03-characters.md").write_text("# Characters\n\nCHARACTERS-SENTINEL\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def responses(self, *items: str) -> Path:
        path = self.tempdir / "responses.txt"
        path.write_text(SEPARATOR.join(items), encoding="utf-8")
        return path

    def test_judge_a_file_with_the_fake_adapter_prints_the_verdict(self) -> None:
        chapter = self.tempdir / "chapter.md"
        chapter.write_text(DRAFT, encoding="utf-8")
        result = run_cli(
            "judge", str(chapter), "--genre", "thriller", "--adapter", "fake", "--fake-responses", str(self.responses(YES))
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertIn("turn_page: yes", result.stdout)
        self.assertIn("the hum", result.stdout)

    def test_brief_command_writes_the_brief(self) -> None:
        result = run_cli("brief", str(self.project), "1")
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertTrue((self.project / "briefs" / "chapter-01.md").exists())

    def test_chapter_command_runs_the_loop_and_reports(self) -> None:
        result = run_cli("chapter", str(self.project), "1", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES)))
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertIn("accepted", result.stdout)
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-01.md").exists())

    def test_chapter_two_fails_closed_until_a_human_approves_chapter_one(self) -> None:
        first = run_cli("chapter", str(self.project), "1", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES)))
        self.assertEqual(0, first.returncode, msg=first.stderr)

        blocked = run_cli("chapter", str(self.project), "2", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES)))
        self.assertEqual(3, blocked.returncode, msg=blocked.stdout + blocked.stderr)
        self.assertIn("approve", blocked.stdout + blocked.stderr)

        approved = run_cli("approve", str(self.project), "chapter-01")
        self.assertEqual(0, approved.returncode, msg=approved.stderr)

        second = run_cli("chapter", str(self.project), "2", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES)))
        self.assertEqual(0, second.returncode, msg=second.stderr)
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-02.md").exists())

    def test_book_command_runs_until_the_human_checkpoint(self) -> None:
        result = run_cli("book", str(self.project), "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES, DRAFT, DISRUPTED, YES)))
        self.assertEqual(3, result.returncode, msg=result.stdout + result.stderr)
        self.assertIn("awaiting", result.stdout)
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-01.md").exists())
        self.assertFalse((self.project / "manuscript" / "chapters" / "chapter-02.md").exists())

    def test_run_phase_command_executes_the_current_phase(self) -> None:
        fresh = self.tempdir / "fresh"
        scaffold_project(fresh, idea="a night-shift analyst in Brussels", adapter="fake", model_name="fake", language="en")
        intake = (
            "=== FILE: ASSUMPTIONS.md ===\n# Assumptions\n\nInferred: thriller.\n\n"
            "=== FILE: artifacts/00-brief.md ===\n# Brief\n\nBRIEF-SENTINEL\n\n"
            "=== FILE: artifacts/01-market-map.md ===\n# Market Map\n\nMARKET-SENTINEL\n\n"
            "=== FILE: artifacts/02-story-engine.md ===\n# Story Engine\n\nENGINE-SENTINEL\n\n"
            "=== STATE ===\ntitle: The Watch Room\ngenre: thriller\n"
        )
        result = run_cli("run-phase", str(fresh), "--fake-responses", str(self.responses(intake)))
        self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
        self.assertIn("Phase 1: Foundation", result.stdout)
        self.assertIn("BRIEF-SENTINEL", (fresh / "artifacts" / "00-brief.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
