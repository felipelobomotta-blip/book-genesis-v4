from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import FakeAdapter  # type: ignore  # noqa: E402
from runner.judge import parse_verdict  # type: ignore  # noqa: E402
from runner.panel import PanelJudge, PanelMember, aggregate  # type: ignore  # noqa: E402


def block(turn_page: str, stopped_at: str = "none", remember=(), flags=(), vs_previous: str = "none") -> str:
    remember_lines = "\n".join(f"  - {item}" for item in remember) or "  []"
    remember_yaml = f"remember:\n{remember_lines}" if remember else "remember: []"
    flags_yaml = "flags: [" + ", ".join(flags) + "]"
    return (
        f"```yaml\nturn_page: {turn_page}\nstopped_at: {stopped_at}\n{remember_yaml}\n{flags_yaml}\n"
        f"vs_previous: {vs_previous}\nvs_anchor: none\n```\n"
    )


class AggregateTests(unittest.TestCase):
    def test_majority_decides_and_flags_need_two_citations_in_a_panel_of_three(self) -> None:
        verdicts = [
            parse_verdict(block("yes", remember=["the hum"])),
            parse_verdict(block("no", stopped_at='"The console blinked."', flags=["hook", "pacing"])),
            parse_verdict(block("no", stopped_at='"The console blinked."', flags=["hook"])),
        ]
        verdict = aggregate(verdicts)
        self.assertFalse(verdict.turn_page)
        self.assertEqual(["hook"], verdict.flags)
        self.assertEqual("The console blinked.", verdict.stopped_at)
        self.assertIn("the hum", verdict.remember)

    def test_a_panel_of_two_counts_any_flag(self) -> None:
        verdicts = [
            parse_verdict(block("yes")),
            parse_verdict(block("no", stopped_at='"Paragraph two."', flags=["dialogue"])),
        ]
        verdict = aggregate(verdicts)
        self.assertEqual(["dialogue"], verdict.flags)
        self.assertFalse(verdict.turn_page)

    def test_unanimous_yes_passes_with_no_flags(self) -> None:
        verdicts = [parse_verdict(block("yes", remember=["a"])) for _ in range(3)]
        verdict = aggregate(verdicts)
        self.assertTrue(verdict.turn_page)
        self.assertEqual([], verdict.flags)
        self.assertEqual("none", verdict.stopped_at)

    def test_vs_previous_follows_the_majority(self) -> None:
        verdicts = [
            parse_verdict(block("yes", vs_previous="better")),
            parse_verdict(block("yes", vs_previous="worse")),
            parse_verdict(block("yes", vs_previous="better")),
        ]
        self.assertEqual("better", aggregate(verdicts).vs_previous)


class PanelJudgeTests(unittest.TestCase):
    def test_each_member_reads_blind_with_its_own_persona(self) -> None:
        adapters = [FakeAdapter([block("yes", remember=["the hum"])]) for _ in range(3)]
        personas = ["the reader who buys thrillers", "the hostile reader", "the casual airport reader"]
        panel = PanelJudge(
            [PanelMember(adapter=adapter, model="", persona=persona) for adapter, persona in zip(adapters, personas)]
        )
        verdict = panel.judge("DISRUPTED-SENTINEL Halden counted the hum.", "He was such a good dog.", "thriller")

        for adapter, persona in zip(adapters, personas):
            prompt = adapter.calls[0].prompt
            self.assertIn(persona, prompt)
            self.assertIn("DISRUPTED-SENTINEL", prompt)
            self.assertNotIn("OUTLINE", prompt)
        self.assertTrue(verdict.turn_page)
        self.assertEqual(3, len(panel.last_verdicts))
        self.assertIn("the hum", verdict.raw)


if __name__ == "__main__":
    unittest.main()
