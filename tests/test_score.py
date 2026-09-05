"""The Genesis Score is computed only from what blind readers did (ADR 0009)."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.score import chapter_rows, genesis_score  # type: ignore  # noqa: E402

PANEL_RAW = """# Reader panel

## genre reader (fake)

```yaml
turn_page: yes
stopped_at: none
remember:
  - the hum
flags: []
vs_previous: none
vs_anchor: none
```

## hostile reader (fake)

```yaml
turn_page: no
stopped_at: the second paragraph
remember: []
flags: [exposition]
vs_previous: none
vs_anchor: none
```

## Aggregate (2 of 3 would turn the page)

```yaml
turn_page: yes
stopped_at: "the second paragraph"
remember:
  - "the hum"
flags: []
vs_previous: none
vs_anchor: none
```
"""
SINGLE_YES = "```yaml\nturn_page: yes\nstopped_at: none\nremember:\n  - the drive south\nflags: []\nvs_previous: better\nvs_anchor: none\n```\n"
SINGLE_NO_MEMORY = "```yaml\nturn_page: yes\nstopped_at: none\nremember: []\nflags: []\nvs_previous: none\nvs_anchor: none\n```\n"


def report(*lines: str) -> str:
    return "# Run Report\n\n## Chapter log\n\n" + "\n".join(lines) + "\n"


def line(number: int, status: str, cycles: int, turn: str = "yes") -> str:
    return f"- chapter {number}: {status} after {cycles} revision cycle(s); judge: panel of 3; last verdict: turn_page={turn}, flags=[], stopped_at=none; file: x"


class ScoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = Path(tempfile.mkdtemp(prefix="book-genesis-score-"))
        (self.project / "evaluations").mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.project, ignore_errors=True)

    def write(self, name: str, text: str) -> None:
        (self.project / "evaluations" / name).write_text(text, encoding="utf-8")

    def test_perfect_book_scores_ten(self) -> None:
        (self.project / "RUN_REPORT.md").write_text(report(line(1, "accepted", 0), line(2, "accepted", 0)), encoding="utf-8")
        self.write("chapter-01-judge-1.md", PANEL_RAW.replace("2 of 3", "3 of 3"))
        self.write("chapter-02-judge-1.md", SINGLE_YES)
        card = genesis_score(self.project)
        self.assertEqual(10.0, card.score)
        self.assertEqual("model readers turned every page", card.band())

    def test_every_component_is_visible_and_weighted(self) -> None:
        # panel 2/3 (0.4 * 0.667), first draft 1 of 2 (0.3 * 0.5), accepted 2 of 2 (0.2), remembered 1 of 2 (0.1 * 0.5)
        (self.project / "RUN_REPORT.md").write_text(report(line(1, "accepted", 0), line(2, "accepted", 2)), encoding="utf-8")
        self.write("chapter-01-judge-1.md", PANEL_RAW)
        self.write("chapter-02-judge-1.md", SINGLE_NO_MEMORY)
        self.write("chapter-02-judge-3.md", SINGLE_NO_MEMORY)
        card = genesis_score(self.project)
        self.assertEqual(6.7, card.score)
        by_key = {component.key: component for component in card.components}
        self.assertEqual("2 of 3 blind readers would turn the page", by_key["panel"].detail)
        self.assertEqual("1 of 2 chapters accepted on the first draft", by_key["first_pass"].detail)
        self.assertEqual("2 of 2 chapters accepted in the end", by_key["accepted"].detail)
        self.assertEqual("1 of 2 chapters left the reader with something specific", by_key["remembered"].detail)
        self.assertEqual([0.4, 0.3, 0.2, 0.1], [component.weight for component in card.components])
        text = card.markdown()
        self.assertIn("**6.7 / 10**", text)
        self.assertIn("(40%)", text)
        self.assertIn("model independence depends on the configured roles", text)

    def test_a_blocked_chapter_is_named_and_capped(self) -> None:
        (self.project / "RUN_REPORT.md").write_text(report(line(1, "accepted", 0), line(2, "blocked", 3, "no")), encoding="utf-8")
        self.write("chapter-01-judge-1.md", PANEL_RAW.replace("2 of 3", "3 of 3"))
        card = genesis_score(self.project)
        self.assertEqual([2], card.blocked)
        self.assertEqual("a chapter never convinced the reader", card.band())
        self.assertLess(card.score, 8.0)

    def test_a_rewritten_chapter_counts_its_last_run(self) -> None:
        (self.project / "RUN_REPORT.md").write_text(report(line(1, "accepted", 2), line(1, "accepted", 0)), encoding="utf-8")
        rows = chapter_rows(self.project / "RUN_REPORT.md")
        self.assertEqual(0, rows[1].cycles)

    def test_no_report_means_no_score_not_a_crash(self) -> None:
        card = genesis_score(self.project)
        self.assertEqual(0, card.chapters)
        self.assertEqual(0.0, card.score)
        self.assertEqual("no chapters were judged", card.band())


if __name__ == "__main__":
    unittest.main()
