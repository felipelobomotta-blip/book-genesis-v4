from pathlib import Path
import re
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.tui import apply_key, banner, physical_rows, supports_interactive  # type: ignore  # noqa: E402
from runner.tui import strip_ansi as module_strip_ansi  # type: ignore  # noqa: E402


def strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class ApplyKeyTests(unittest.TestCase):
    """The pure navigation math behind the arrow-key menu. No terminal involved."""

    def test_down_moves_to_the_next_option(self) -> None:
        self.assertEqual(1, apply_key("down", 0, 3))

    def test_up_moves_to_the_previous_option(self) -> None:
        self.assertEqual(0, apply_key("up", 1, 3))

    def test_down_wraps_from_the_last_option_to_the_first(self) -> None:
        self.assertEqual(0, apply_key("down", 2, 3))

    def test_up_wraps_from_the_first_option_to_the_last(self) -> None:
        self.assertEqual(2, apply_key("up", 0, 3))

    def test_a_digit_jumps_straight_to_that_option(self) -> None:
        self.assertEqual(2, apply_key("3", 0, 5))

    def test_an_out_of_range_digit_is_ignored(self) -> None:
        self.assertEqual(0, apply_key("9", 0, 3))

    def test_an_unrecognised_key_does_not_move_the_selection(self) -> None:
        self.assertEqual(1, apply_key("x", 1, 3))

    def test_a_sequence_of_keys_lands_on_the_expected_option(self) -> None:
        # 0 -> down -> 1 -> down -> 2 -> down -> 3 -> up -> 2
        selected = 0
        for key in ("down", "down", "down", "up"):
            selected = apply_key(key, selected, 4)
        self.assertEqual(2, selected)


class BannerTests(unittest.TestCase):
    def test_names_the_product(self) -> None:
        # The title is letter-spaced ("B O O K   G E N E S I S") for the banner look.
        text = banner(color=False).upper().replace(" ", "")
        self.assertIn("BOOK", text)
        self.assertIn("GENESIS", text)

    def test_is_a_closed_box_the_same_width_on_every_line(self) -> None:
        lines = banner(color=False).splitlines()
        widths = {len(line) for line in lines}
        self.assertEqual(1, len(widths), msg=lines)

    def test_color_wraps_the_text_without_changing_it(self) -> None:
        plain = banner(color=False)
        colored = banner(color=True)
        self.assertNotEqual(plain, colored)
        self.assertEqual(plain, strip_ansi(colored))


class PhysicalRowsTests(unittest.TestCase):
    """The bug seen in the first live run: a label longer than the terminal is wide wraps onto
    a second row, and a redraw that moves up by logical lines comes back one row short."""

    def test_a_short_line_is_one_row(self) -> None:
        self.assertEqual(1, physical_rows("hello", 80))

    def test_a_line_exactly_as_wide_as_the_terminal_is_still_one_row(self) -> None:
        self.assertEqual(1, physical_rows("x" * 80, 80))

    def test_one_character_more_wraps_onto_a_second_row(self) -> None:
        self.assertEqual(2, physical_rows("x" * 81, 80))

    def test_the_label_from_the_live_run_wraps_in_a_narrow_terminal(self) -> None:
        label = "  > ChatGPT / Codex subscription (OAuth through the Codex CLI, no key) [detected]"
        self.assertEqual(2, physical_rows(label, 60))
        self.assertEqual(1, physical_rows(label, 120))

    def test_color_codes_take_no_space(self) -> None:
        colored = "\x1b[36m>\x1b[0m " + "\x1b[1m" + "x" * 78 + "\x1b[0m"
        self.assertEqual(1, physical_rows(colored, 80))

    def test_an_empty_line_is_one_row(self) -> None:
        self.assertEqual(1, physical_rows("", 80))

    def test_strip_ansi_removes_cursor_and_color_codes(self) -> None:
        self.assertEqual("abc", module_strip_ansi("\x1b[3A\x1b[2K\x1b[36mabc\x1b[0m"))


class SupportsInteractiveTests(unittest.TestCase):
    def test_false_when_stdin_is_not_a_tty(self) -> None:
        class NotATty:
            def isatty(self) -> bool:
                return False

        self.assertFalse(supports_interactive(stdin=NotATty(), stdout=NotATty()))

    def test_true_when_both_sides_are_a_tty(self) -> None:
        class ATty:
            def isatty(self) -> bool:
                return True

        self.assertTrue(supports_interactive(stdin=ATty(), stdout=ATty()))

    def test_false_when_only_one_side_is_a_tty(self) -> None:
        class ATty:
            def isatty(self) -> bool:
                return True

        class NotATty:
            def isatty(self) -> bool:
                return False

        self.assertFalse(supports_interactive(stdin=ATty(), stdout=NotATty()))
        self.assertFalse(supports_interactive(stdin=NotATty(), stdout=ATty()))

    def test_a_stream_with_no_isatty_method_is_treated_as_not_interactive(self) -> None:
        self.assertFalse(supports_interactive(stdin=object(), stdout=object()))


if __name__ == "__main__":
    unittest.main()
