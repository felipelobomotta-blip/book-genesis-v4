"""The entry point: `new`/`resume` open the guided session, everything else is the old CLI (ADR 0009)."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from runner import app  # type: ignore  # noqa: E402
from runner.filesystem import scaffold_project  # type: ignore  # noqa: E402
from test_session import (  # type: ignore  # noqa: E402
    ARCHITECTURE,
    AUDIT,
    CHAPTER_ONE,
    CHAPTER_TWO,
    FOUNDATION,
    INTAKE,
    PACKAGE,
    SCORE,
    SEPARATOR,
    RecordingView,
)


class AppRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-app-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def responses(self, *items: str) -> Path:
        path = self.tempdir / "responses.txt"
        path.write_text(SEPARATOR.join(items), encoding="utf-8")
        return path

    def test_new_creates_the_project_and_runs_the_session(self) -> None:
        project = self.tempdir / "book"
        view = RecordingView(interactive=False)
        code = app.session_main(
            [
                "new",
                "--idea", "a night-shift analyst in Brussels",
                "--language", "en",
                "--path", str(project),
                "--fake-responses", str(self.responses(INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE, *CHAPTER_TWO, AUDIT, SCORE, PACKAGE)),
            ],
            view=view,
        )
        self.assertEqual(0, code, msg=view.calls)
        self.assertTrue((project / "manuscript" / "chapters" / "chapter-02.md").exists())
        self.assertEqual([], view.checkpoints)  # no terminal: autonomous, exactly as ADR 0002
        self.assertEqual(10.0, view.card.score)

    def test_resume_continues_an_existing_project(self) -> None:
        project = self.tempdir / "book"
        scaffold_project(project, idea="an analyst", adapter="auto", model_name="auto", language="en")
        view = RecordingView(interactive=False)
        code = app.session_main(
            ["resume", str(project), "--chapters", "1",
             "--fake-responses", str(self.responses(INTAKE, FOUNDATION, ARCHITECTURE, *CHAPTER_ONE))],
            view=view,
        )
        self.assertEqual(0, code, msg=view.calls)
        self.assertTrue((project / "manuscript" / "chapters" / "chapter-01.md").exists())

    def test_resume_without_a_project_fails_with_a_readable_message(self) -> None:
        view = RecordingView(interactive=False)
        code = app.session_main(["resume", str(self.tempdir / "nowhere")], view=view)
        self.assertEqual(1, code)
        self.assertIn("book-genesis new", view.calls[-1][1])

    def test_new_without_an_idea_refuses_instead_of_inventing_one(self) -> None:
        # The person's own idea is the one thing the runner never makes up (2026-09-03).
        view = RecordingView(interactive=False)
        view.ask = lambda prompt, default="": ""
        code = app.session_main(["new", "--path", str(self.tempdir / "x")], view=view)
        self.assertEqual(2, code)
        self.assertIn("idea is required", view.calls[-1][1])
        self.assertFalse((self.tempdir / "x").exists())

    def test_the_front_door_help_reads_like_a_sentence(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "runner", "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), check=False, timeout=60,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)
        for line in ("book-genesis setup", "book-genesis new", "book-genesis resume", "--yes", "--human"):
            self.assertIn(line, result.stdout)
        self.assertNotIn("prepare-agent-packet", result.stdout)  # not the argparse dump
        self.assertLess(len(result.stdout.splitlines()), 30)

    def test_other_commands_still_reach_the_command_layer(self) -> None:
        project = self.tempdir / "doctored"
        scaffold_project(project, idea="x", adapter="fake", model_name="fake", language="en")
        self.assertEqual(0, app.main(["validate", str(project)]))

    def test_the_module_entry_point_runs_the_app(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "runner", "new", "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(REPO_ROOT), check=False, timeout=60,
        )
        self.assertEqual(0, result.returncode, msg=result.stderr)
        self.assertIn("--yes", result.stdout)
        self.assertIn("--plain", result.stdout)


if __name__ == "__main__":
    unittest.main()
