from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.brief import build_chapter_brief  # type: ignore  # noqa: E402
from runner.filesystem import scaffold_project  # type: ignore  # noqa: E402


OUTLINE = """# Outline

## Macro structure

Three acts, one narrator.

## Chapter 1: The Watch Room

CH1-SENTINEL Halden watches the dashboards and laughs.

## Chapter 2: The Drive

CH2-SENTINEL Halden drives Yusuf south; the dog on the motorway; ~3,200 words.

## Chapter 3: Silence

CH3-SENTINEL The Listeners are never described.
"""


class BriefTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = Path(tempfile.mkdtemp(prefix="book-genesis-brief-"))
        scaffold_project(self.project, idea="collapse fiction", adapter="fake", model_name="fake", language="en")
        state = self.project / "PROJECT_STATE.yaml"
        state.write_text(state.read_text(encoding="utf-8").replace('genre: ""', 'genre: "thriller"'), encoding="utf-8")
        (self.project / "artifacts" / "05-outline.md").write_text(OUTLINE, encoding="utf-8")
        (self.project / "artifacts" / "02-story-engine.md").write_text("# Story Engine\n\nENGINE-SENTINEL\n", encoding="utf-8")
        (self.project / "artifacts" / "03-characters.md").write_text("# Characters\n\nCHARACTERS-SENTINEL\n", encoding="utf-8")
        chapter_one = "# Chapter 1\n\nEARLY-SENTINEL " + ("word " * 400) + "LATE-SENTINEL the last line.\n"
        (self.project / "manuscript" / "chapters" / "chapter-01.md").write_text(chapter_one, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.project, ignore_errors=True)

    def test_brief_holds_only_this_chapter_and_the_tail_of_the_last_one(self) -> None:
        brief = build_chapter_brief(self.project, 2)
        self.assertIn("CH2-SENTINEL", brief)
        self.assertNotIn("CH1-SENTINEL", brief)
        self.assertNotIn("CH3-SENTINEL", brief)
        self.assertIn("LATE-SENTINEL", brief)
        self.assertNotIn("EARLY-SENTINEL", brief)
        self.assertIn("ENGINE-SENTINEL", brief)
        self.assertIn("CHARACTERS-SENTINEL", brief)

    def test_brief_carries_the_genre_constants(self) -> None:
        brief = build_chapter_brief(self.project, 2)
        self.assertIn("1500", brief)
        self.assertIn("3500", brief)

    def test_brief_is_written_as_a_project_artifact(self) -> None:
        build_chapter_brief(self.project, 2)
        self.assertTrue((self.project / "briefs" / "chapter-02.md").exists())

    def test_first_chapter_has_no_previous_tail(self) -> None:
        brief = build_chapter_brief(self.project, 1)
        self.assertIn("CH1-SENTINEL", brief)
        self.assertNotIn("LATE-SENTINEL", brief)

    def test_chapter_missing_from_outline_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            build_chapter_brief(self.project, 9)

    def test_bold_portuguese_chapter_markers_are_understood(self) -> None:
        # What a real architecture run produced (2026-09-02): bold lines, not headings.
        bold_outline = (
            "# 05 — Estrutura e Outline\n\n## Macroestrutura\n\nQuatro partes.\n\n"
            "## Outline por capítulo\n\n### PARTE I — A COINCIDÊNCIA (cap. 1–9)\n\n---\n\n"
            "**Capítulo 1 — 3h14**\n*Modo: caçada. ~2.200 palavras.*\n\n"
            "CH1-BOLD-SENTINEL Rita confere o carimbo de tempo três vezes.\n\n---\n\n"
            "**Capítulo 2 — Assinatura duplicada**\n\nCH2-BOLD-SENTINEL Rita reconstrói a sincronia.\n\n"
            "### PARTE II — A PENEIRA (cap. 10–19)\n\n**Capítulo 10 — Linhagem**\n\nCH10-BOLD-SENTINEL\n\n"
            "## Mapa de tensão\n\nSobe.\n"
        )
        (self.project / "artifacts" / "05-outline.md").write_text(bold_outline, encoding="utf-8")
        brief = build_chapter_brief(self.project, 2)
        self.assertIn("CH2-BOLD-SENTINEL", brief)
        self.assertNotIn("CH1-BOLD-SENTINEL", brief)
        self.assertNotIn("CH10-BOLD-SENTINEL", brief)
        self.assertNotIn("PARTE II", brief)


if __name__ == "__main__":
    unittest.main()
