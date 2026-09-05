from pathlib import Path
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import (  # type: ignore  # noqa: E402
    AwaitingManual,
    AdapterError,
    ClaudeCliAdapter,
    CodexCliAdapter,
    GenericCliAdapter,
    ManualAdapter,
    _run,
    _terminate_timed_out_process,
    command_template_argv,
    resolve_repo_relative_argv,
    resolve_repo_relative_tokens,
)


class GenericCliAdapterTests(unittest.TestCase):
    def test_command_template_fills_the_model(self) -> None:
        adapter = GenericCliAdapter("opencode", "opencode run --model {model}")
        self.assertEqual("opencode run --model gpt-x", adapter.render_command("gpt-x"))

    def test_runs_any_command_with_the_prompt_on_stdin_and_reads_stdout(self) -> None:
        template = f'"{sys.executable}" -c "import sys; print(sys.stdin.read().upper())"'
        adapter = GenericCliAdapter("shout", template)
        self.assertEqual("HELLO WORLD", adapter.complete("hello world", model=""))

    def test_repo_relative_script_is_resolved_from_another_working_directory(self) -> None:
        template = "python runner/bridge_gemini.py {model}"
        adapter = GenericCliAdapter("gemini", template)
        # The token resolves to an absolute path under REPO_ROOT no matter the CWD.
        resolved = resolve_repo_relative_argv(command_template_argv(adapter.command_template))
        script = resolved[1]
        self.assertTrue(Path(script).is_absolute())
        self.assertTrue(Path(script).exists())

    def test_plain_tokens_are_left_alone(self) -> None:
        self.assertEqual(resolve_repo_relative_tokens("foo --bar --model x"), "foo --bar --model x")

    def test_argv_preserves_spaces_in_script_and_model_without_shell_interpolation(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="root with spaces "))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        script = root / "echo arguments.py"
        script.write_text("import sys\nprint(repr(sys.argv[1:]))\n", encoding="utf-8")
        model = "model with spaces; not-a-shell-command"
        adapter = GenericCliAdapter("echo", f'"{sys.executable}" "{script}" --model {{model}}')
        self.assertEqual(repr(["--model", model]), adapter.complete("unused", model=model))

    def test_quoted_program_files_executable_stays_one_argv_element(self) -> None:
        adapter = GenericCliAdapter("tool", '"C:\\Program Files\\Tool\\tool.exe" --model {model}')
        with patch("runner.adapters.shutil.which", return_value=r"C:\Program Files\Tool\tool.exe"):
            self.assertEqual(
                [r"C:\Program Files\Tool\tool.exe", "--model", "model with spaces"],
                adapter.build_command("model with spaces"),
            )

    def test_repo_relative_argv_preserves_a_single_space_containing_path(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="repo path with spaces "))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        target = root / "bridge script.py"
        target.write_text("", encoding="utf-8")
        with patch("runner.adapters.REPO_ROOT", root):
            self.assertEqual([str(target)], resolve_repo_relative_argv(["bridge script.py"]))


class BuiltInCliIsolationTests(unittest.TestCase):
    def test_claude_explicitly_disables_its_tools(self) -> None:
        # The command shape is a unit contract; no installed Claude CLI is required.
        with patch("runner.adapters._resolve", return_value=["claude"]):
            command = ClaudeCliAdapter().build_command()
        self.assertEqual("", command[command.index("--tools") + 1])
        self.assertIn("--safe-mode", command)
        self.assertIn("--disable-slash-commands", command)

    def test_codex_uses_the_supported_read_only_ephemeral_boundary(self) -> None:
        # The command shape is a unit contract; no installed Codex CLI is required.
        with patch("runner.adapters._resolve", return_value=["codex"]):
            command = CodexCliAdapter().build_command()
        self.assertIn("--ephemeral", command)
        self.assertEqual("read-only", command[command.index("-s") + 1])
        self.assertIn("--ignore-user-config", command)
        self.assertNotIn("--ignore-rules", command)

    def test_claude_uses_a_temporary_working_directory(self) -> None:
        adapter = ClaudeCliAdapter(timeout_seconds=1)
        completed = __import__("subprocess").CompletedProcess(["claude"], 0, "answer", "")
        with patch("runner.adapters.shutil.which", return_value="claude"), patch("runner.adapters._run", return_value=completed) as run:
            self.assertEqual("answer", adapter.complete("prompt"))
        self.assertNotEqual(str(Path.cwd()), run.call_args.kwargs["cwd"])
        self.assertIn("book-genesis-claude-", run.call_args.kwargs["cwd"])

    def test_timeout_cleanup_targets_only_the_created_pid_tree(self) -> None:
        process = type("Process", (), {"pid": 4242, "poll": lambda self: None})()
        with patch("runner.adapters.os.name", "nt"), patch("runner.adapters.subprocess.run") as taskkill:
            _terminate_timed_out_process(process)
        taskkill.assert_called_once()
        self.assertEqual(["taskkill", "/PID", "4242", "/T", "/F"], taskkill.call_args.args[0])

    def test_timed_out_run_reaps_only_its_own_wrapper_tree(self) -> None:
        class TimedOutProcess:
            pid = 5151
            returncode = None

            def poll(self):
                return None

            def communicate(self, input=None, timeout=None):
                if input is not None:
                    raise __import__("subprocess").TimeoutExpired("wrapper", timeout)
                self.returncode = -9
                return "", ""

            def kill(self):
                self.returncode = -9

        process = TimedOutProcess()
        with patch("runner.adapters.os.name", "nt"), patch("runner.adapters.subprocess.Popen", return_value=process), patch("runner.adapters.subprocess.run") as taskkill:
            with self.assertRaises(__import__("subprocess").TimeoutExpired):
                _run(["wrapper"], "prompt", timeout_seconds=1)
        self.assertEqual(["taskkill", "/PID", "5151", "/T", "/F"], taskkill.call_args.args[0])

    def test_timeout_remains_an_adapter_error_when_temp_cleanup_is_locked(self) -> None:
        class LockedDirectory:
            name = "locked-temp"

            def cleanup(self):
                raise PermissionError("still locked")

        adapter = ClaudeCliAdapter(timeout_seconds=1)
        with patch("runner.adapters.tempfile.TemporaryDirectory", return_value=LockedDirectory()), patch(
            "runner.adapters._run", side_effect=__import__("subprocess").TimeoutExpired("claude", 1)
        ), patch("runner.adapters._resolve", return_value=["claude"]):
            with self.assertRaisesRegex(AdapterError, "claude timed out"):
                adapter.complete("prompt")

    @unittest.skipUnless(os.name == "nt", "Windows process-tree cleanup")
    def test_windows_timeout_reaps_an_innocuous_child_process_tree(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="book-genesis-timeout-child-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        script = root / "parent.py"
        script.write_text(
            "import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
            "time.sleep(30)\n",
            encoding="utf-8",
        )
        started = time.monotonic()
        with self.assertRaises(__import__("subprocess").TimeoutExpired):
            _run([sys.executable, str(script)], "", timeout_seconds=1)
        self.assertLess(time.monotonic() - started, 8)


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
