from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import FakeAdapter  # type: ignore  # noqa: E402
from runner.judge import judge_chapter, parse_verdict  # type: ignore  # noqa: E402


VERDICT_BLOCK = """The reader has finished. Answers follow.

```yaml
turn_page: yes
stopped_at: none
remember:
  - the dog on the motorway
  - Yusuf singing at the gas station
flags:
  - dialogue
vs_previous: better
vs_anchor: none
```
"""


class ParseVerdictTests(unittest.TestCase):
    def test_reads_reader_answers_from_yaml_block(self) -> None:
        verdict = parse_verdict(VERDICT_BLOCK)
        self.assertTrue(verdict.turn_page)
        self.assertEqual("none", verdict.stopped_at)
        self.assertEqual(
            ["the dog on the motorway", "Yusuf singing at the gas station"],
            verdict.remember,
        )
        self.assertEqual(["dialogue"], verdict.flags)
        self.assertEqual("better", verdict.vs_previous)
        self.assertEqual("none", verdict.vs_anchor)

    def test_a_reader_who_stopped_is_a_no(self) -> None:
        text = (
            "```yaml\n"
            "turn_page: no\n"
            'stopped_at: "the second paragraph, where the narrator explains the rule"\n'
            "remember: []\n"
            "flags: [hook, ai_pattern]\n"
            "vs_previous: none\n"
            "vs_anchor: none\n"
            "```\n"
        )
        verdict = parse_verdict(text)
        self.assertFalse(verdict.turn_page)
        self.assertEqual("the second paragraph, where the narrator explains the rule", verdict.stopped_at)
        self.assertEqual([], verdict.remember)
        self.assertEqual(["hook", "ai_pattern"], verdict.flags)

    def test_missing_block_is_an_error_not_a_pass(self) -> None:
        with self.assertRaises(ValueError):
            parse_verdict("Great chapter, loved it, 9.5/10!")


class JudgeChapterTests(unittest.TestCase):
    def test_judge_receives_prose_and_previous_tail(self) -> None:
        adapter = FakeAdapter([VERDICT_BLOCK])
        verdict = judge_chapter(
            prose="Halden counted to forty-six before the lockstep broke.",
            previous_tail="He was such a good dog.",
            genre="thriller",
            adapter=adapter,
            model="sonnet",
        )
        sent = adapter.calls[0]
        self.assertIn("Halden counted to forty-six before the lockstep broke.", sent.prompt)
        self.assertIn("He was such a good dog.", sent.prompt)
        self.assertEqual("sonnet", sent.model)
        self.assertTrue(verdict.turn_page)

    def test_judge_compares_against_previous_draft_when_given(self) -> None:
        adapter = FakeAdapter([VERDICT_BLOCK])
        judge_chapter(
            prose="Draft two of the chapter.",
            previous_tail="",
            genre="thriller",
            adapter=adapter,
            model="sonnet",
            previous_draft="Draft one of the chapter.",
        )
        sent = adapter.calls[0].prompt
        self.assertIn("Draft one of the chapter.", sent)
        self.assertIn("Draft two of the chapter.", sent)


if __name__ == "__main__":
    unittest.main()
