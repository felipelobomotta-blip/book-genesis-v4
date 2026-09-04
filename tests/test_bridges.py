"""The bridges that let any model CLI drive the runner (ADR 0010).

Parsing only: the subprocess itself is proved by the real probes recorded in the ADR.
"""
from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner import bridge_antigravity as agy  # type: ignore  # noqa: E402
from runner import bridge_hermes as hermes  # type: ignore  # noqa: E402
from runner.constants import USER_ADAPTERS_ENV, load_generic_adapters, user_adapters_path  # type: ignore  # noqa: E402

# Exactly what agy 1.1.26 wrote on 2026-09-04, trimmed.
AGY_SUCCESS = (
    '{"event":"init","conversation_id":"9cd2","init":{"cwd":"C:\\\\Windows"}}\n'
    '{"event":"step_update","step_update":{"step_index":0,"state":"DONE","step_type":"user_input"}}\n'
    '{"event":"result","result":{"conversation_id":"9cd2","status":"SUCCESS","response":"OK\\n","duration_seconds":2.9}}\n'
)
AGY_QUOTA = (
    '{"event":"init","conversation_id":"d9eb"}\n'
    '{"event":"result","result":{"status":"ERROR","response":"","error":"Individual quota reached. '
    'Please upgrade your subscription to increase your limits. Resets in 3h17m45s."}}\n'
)


class AntigravityTests(unittest.TestCase):
    def test_the_prompt_goes_in_as_one_ndjson_event_never_on_the_command_line(self) -> None:
        encoded = agy.encode_prompt("write chapter 1\nwith two lines")
        self.assertTrue(encoded.endswith("\n"))
        self.assertEqual({"event": "user", "message": {"content": "write chapter 1\nwith two lines"}}, __import__("json").loads(encoded))
        command = agy.build_command("gemini-3.1-pro-high")
        self.assertIn("--input-format", command)
        self.assertIn("stream-json", command)
        self.assertEqual(["--model", "gemini-3.1-pro-high"], command[-2:])
        self.assertTrue(all("write chapter 1" not in part for part in command))

    def test_a_successful_stream_yields_the_response(self) -> None:
        self.assertEqual(("SUCCESS", "OK\n", None), agy.parse_result(AGY_SUCCESS))

    def test_an_exhausted_quota_is_an_error_with_its_reason_not_an_empty_chapter(self) -> None:
        status, response, error = agy.parse_result(AGY_QUOTA)
        self.assertEqual("ERROR", status)
        self.assertEqual("", response)
        self.assertIn("quota reached", error)

    def test_a_stream_without_a_result_event_fails_loudly(self) -> None:
        status, _, error = agy.parse_result('{"event":"init"}\nnot json at all\n')
        self.assertEqual("NO_RESULT", status)
        self.assertIn("no result event", error)

    def test_no_model_means_no_model_flag(self) -> None:
        self.assertNotIn("--model", agy.build_command(""))


class HermesTests(unittest.TestCase):
    def test_the_cli_own_warnings_are_not_part_of_the_prose(self) -> None:
        # Measured 2026-09-04: hermes prints "Warning: Unknown toolsets: bfl" on stdout first.
        self.assertEqual("OK", hermes.strip_noise("Warning: Unknown toolsets: bfl\nOK\n"))
        self.assertEqual("The chapter.", hermes.strip_noise("Warning: a\nNote: b\n\nThe chapter."))

    def test_a_warning_inside_the_prose_is_kept(self) -> None:
        prose = "He read the sign.\nWarning: high voltage.\nHe stepped back."
        self.assertEqual(prose, hermes.strip_noise(prose))

    def test_the_prompt_goes_on_stdin_and_the_model_is_a_flag(self) -> None:
        self.assertEqual(["hermes", "chat", "-Q", "--query-file", "-"], hermes.build_command(""))
        self.assertEqual(["-m", "anthropic/claude-sonnet-4-5"], hermes.build_command("anthropic/claude-sonnet-4-5")[-2:])


class UserAdaptersTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-adapters-"))
        self.previous = os.environ.get(USER_ADAPTERS_ENV)
        os.environ[USER_ADAPTERS_ENV] = str(self.tempdir / "adapters.yaml")

    def tearDown(self) -> None:
        if self.previous is None:
            os.environ.pop(USER_ADAPTERS_ENV, None)
        else:
            os.environ[USER_ADAPTERS_ENV] = self.previous
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_a_person_declares_their_own_cli_without_touching_the_repository(self) -> None:
        user_adapters_path().write_text(
            "my-cli:\n  command: python runner/bridge_hermes.py {model}\n", encoding="utf-8"
        )
        adapters = load_generic_adapters()
        self.assertEqual("python runner/bridge_hermes.py {model}", adapters["my-cli"])
        self.assertIn("gemini", adapters)  # the repository's own entries are still there

    def test_the_person_wins_over_the_repository_default(self) -> None:
        user_adapters_path().write_text("gemini:\n  command: my-own-gemini {model}\n", encoding="utf-8")
        self.assertEqual("my-own-gemini {model}", load_generic_adapters()["gemini"])

    def test_no_user_file_changes_nothing(self) -> None:
        self.assertNotIn("my-cli", load_generic_adapters())


if __name__ == "__main__":
    unittest.main()
