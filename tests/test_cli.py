import os
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

    def test_chapter_two_runs_without_approval_by_default(self) -> None:
        first = run_cli("chapter", str(self.project), "1", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES)))
        self.assertEqual(0, first.returncode, msg=first.stderr)

        second = run_cli("chapter", str(self.project), "2", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES)))
        self.assertEqual(0, second.returncode, msg=second.stdout + second.stderr)
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-02.md").exists())

    def test_human_flag_fails_closed_until_approved(self) -> None:
        first = run_cli("chapter", str(self.project), "1", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES)))
        self.assertEqual(0, first.returncode, msg=first.stderr)

        blocked = run_cli(
            "chapter", str(self.project), "2", "--human", "--fake-responses", str(self.responses(DRAFT, DISRUPTED, YES))
        )
        self.assertEqual(3, blocked.returncode, msg=blocked.stdout + blocked.stderr)
        self.assertIn("approve", blocked.stdout + blocked.stderr)

        approved = run_cli("approve", str(self.project), "chapter-01")
        self.assertEqual(0, approved.returncode, msg=approved.stderr)

    def test_book_command_writes_every_chapter_by_default(self) -> None:
        # With fake responses every role shares one adapter, so the panel for chapter 1 reads
        # three responses (one per persona) after writer + disruptor.
        responses = [DRAFT, DISRUPTED, YES, YES, YES, DRAFT, DISRUPTED, YES]
        result = run_cli("book", str(self.project), "--fake-responses", str(self.responses(*responses)))
        self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
        self.assertIn("completed", result.stdout)
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-02.md").exists())

    def test_manual_adapter_lets_a_chat_only_user_paste_each_answer(self) -> None:
        answers = {"writer": DRAFT, "disruptor": DISRUPTED, "judge": YES}
        result = None
        for _ in range(6):
            result = run_cli("chapter", str(self.project), "1", "--manual")
            if result.returncode != 5:
                break
            prompts = sorted((self.project / "work" / "manual").glob("*.prompt.md"))
            waiting = [p for p in prompts if not p.with_name(p.name.replace(".prompt.md", ".response.md")).exists()]
            self.assertEqual(1, len(waiting), msg=[p.name for p in prompts])
            role = waiting[0].name.rsplit("-", 1)[1].replace(".prompt.md", "")
            self.assertIn(role, answers, msg=waiting[0].name)
            waiting[0].with_name(waiting[0].name.replace(".prompt.md", ".response.md")).write_text(answers[role], encoding="utf-8")
        assert result is not None
        self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
        self.assertTrue((self.project / "manuscript" / "chapters" / "chapter-01.md").exists())

    def test_new_runs_from_idea_to_chapters_with_progress(self) -> None:
        intake = (
            "=== FILE: ASSUMPTIONS.md ===\n# Assumptions\n\nInferred: thriller.\n\n"
            "=== FILE: artifacts/00-brief.md ===\n# Brief\n\nBRIEF-SENTINEL\n\n"
            "=== FILE: artifacts/01-market-map.md ===\n# Market Map\n\nMARKET-SENTINEL\n\n"
            "=== FILE: artifacts/02-story-engine.md ===\n# Story Engine\n\nENGINE-SENTINEL\n\n"
            "=== STATE ===\ntitle: The Watch Room\ngenre: thriller\nlanguage: en\n"
        )
        foundation = (
            "=== FILE: artifacts/03-characters.md ===\n# Characters\n\nCHARACTERS-SENTINEL\n\n"
            "=== FILE: artifacts/04-theme.md ===\n# Theme\n\nTHEME-SENTINEL\n\n"
            "=== FILE: artifacts/06-emotional-curve.md ===\n# Curve\n\nCURVE-SENTINEL\n"
        )
        architecture = (
            "=== FILE: artifacts/05-outline.md ===\n" + OUTLINE + "\n"
            "=== FILE: artifacts/07-opening-strategy.md ===\n# Opening\n\nOPENING-SENTINEL\n"
        )
        audit = "=== FILE: artifacts/08-adversarial-audit.md ===\n# Audit\n\nAUDIT-SENTINEL\n"
        score = "=== FILE: artifacts/09-genesis-score-codex.md ===\n# Diagnostic\n\nSCORE-SENTINEL\n"
        package = "=== FILE: artifacts/10-editorial-package.md ===\n# Package\n\nPACKAGE-SENTINEL\n"
        responses = [
            intake, foundation, architecture,
            DRAFT, DISRUPTED, YES, YES, YES,
            DRAFT, DISRUPTED, YES,
            audit, score, package,
        ]
        project = self.tempdir / "new-book"
        result = run_cli(
            "new",
            "--idea", "a night-shift analyst in Brussels",
            "--language", "en",
            "--path", str(project),
            "--fake-responses", str(self.responses(*responses)),
        )
        self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
        self.assertTrue((project / "manuscript" / "chapters" / "chapter-02.md").exists())
        self.assertIn("Phase 0", result.stdout)
        self.assertIn("chapter 1", result.stdout)
        self.assertIn("chapter 2", result.stdout)
        self.assertIn("RUN_REPORT.md", result.stdout)
        self.assertIn("PACKAGE-SENTINEL", (project / "artifacts" / "10-editorial-package.md").read_text(encoding="utf-8"))
        self.assertIn("completed", result.stdout)

    def test_book_genesis_console_script_is_declared(self) -> None:
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('book-genesis = "runner.cli:main"', pyproject)

    def test_judge_command_resolves_an_explicit_provider_from_the_user_config(self) -> None:
        # Regression: standalone `judge --adapter <name>` used to skip user_config entirely,
        # so a provider from `setup` (openai, deepseek, ...) failed with "unknown adapter"
        # instead of actually being tried. Port 1 refuses fast, so this proves the name
        # resolved to a real HTTP attempt without needing a working key or network.
        config_path = self.tempdir / "judge-user-config.yaml"
        config_path.write_text(
            "provider_myapi:\n  type: openai\n  base_url: http://127.0.0.1:1\n  api_key: sk-test\n",
            encoding="utf-8",
        )
        chapter = self.tempdir / "chapter.md"
        chapter.write_text(DRAFT, encoding="utf-8")
        env = dict(os.environ)
        env["BOOK_GENESIS_CONFIG"] = str(config_path)
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "runner" / "cli.py"), "judge", str(chapter), "--genre", "thriller", "--adapter", "myapi"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, env=env, timeout=20,
        )
        combined = (result.stdout + result.stderr).lower()
        self.assertNotIn("unknown adapter", combined, msg=combined)

    def test_doctor_reports_adapters_and_plan(self) -> None:
        result = run_cli("doctor")
        self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)
        self.assertIn("claude", result.stdout)
        self.assertIn("codex", result.stdout)
        self.assertIn("writer", result.stdout)
        self.assertIn("judge", result.stdout)

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
