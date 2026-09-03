from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import AwaitingManual, GenericCliAdapter, ManualAdapter  # type: ignore  # noqa: E402


class GenericCliAdapterTests(unittest.TestCase):
    def test_command_template_fills_the_model(self) -> None:
        adapter = GenericCliAdapter("opencode", "opencode run --model {model}")
        self.assertEqual("opencode run --model gpt-x", adapter.render_command("gpt-x"))

    def test_runs_any_command_with_the_prompt_on_stdin_and_reads_stdout(self) -> None:
        template = f'"{sys.executable}" -c "import sys; print(sys.stdin.read().upper())"'
        adapter = GenericCliAdapter("shout", template)
        self.assertEqual("HELLO WORLD", adapter.complete("hello world", model=""))


class ManualAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-manual-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_first_call_writes_the_prompt_and_stops(self) -> None:
        adapter = ManualAdapter(self.tempdir / "manual", role="writer")
        with self.assertRaises(AwaitingManual) as context:
            adapter.complete("PROMPT-SENTINEL write chapter one", model="")
        exc = context.exception
        self.assertTrue(exc.prompt_path.exists())
        self.assertIn("PROMPT-SENTINEL", exc.prompt_path.read_text(encoding="utf-8"))
        self.assertTrue(exc.prompt_path.name.endswith("-writer.prompt.md"))
        self.assertTrue(exc.response_path.name.endswith("-writer.response.md"))
        self.assertFalse(exc.response_path.exists())

    def test_second_call_returns_the_pasted_response(self) -> None:
        adapter = ManualAdapter(self.tempdir / "manual", role="writer")
        try:
            adapter.complete("PROMPT-SENTINEL", model="")
        except AwaitingManual as exc:
            exc.response_path.write_text("# Chapter 1\n\nPasted by a human.\n", encoding="utf-8")
        self.assertEqual("# Chapter 1\n\nPasted by a human.", adapter.complete("PROMPT-SENTINEL", model="").strip())

    def test_a_different_prompt_is_a_different_file(self) -> None:
        adapter = ManualAdapter(self.tempdir / "manual", role="judge")
        paths = []
        for prompt in ("first", "second"):
            try:
                adapter.complete(prompt, model="")
            except AwaitingManual as exc:
                paths.append(exc.prompt_path)
        self.assertNotEqual(paths[0], paths[1])


if __name__ == "__main__":
    unittest.main()
