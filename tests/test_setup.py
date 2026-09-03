from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.onboarding import Detection  # type: ignore  # noqa: E402
from runner.setup import run_setup  # type: ignore  # noqa: E402
from runner.userconfig import load_user_config  # type: ignore  # noqa: E402


class ScriptedIO:
    def __init__(self, answers, secrets=()) -> None:
        self.answers = list(answers)
        self.secrets = list(secrets)
        self.shown = []

    def ask(self, prompt: str, default: str = "") -> str:
        self.shown.append(prompt)
        if not self.answers:
            return default
        answer = self.answers.pop(0)
        return answer if answer != "" else default

    def secret(self, prompt: str) -> str:
        self.shown.append(prompt)
        return self.secrets.pop(0) if self.secrets else ""

    def say(self, text: str = "") -> None:
        self.shown.append(text)

    @property
    def transcript(self) -> str:
        return "\n".join(self.shown)


BOTH_CLIS = [
    Detection("claude", "cli", "Claude Code", "on PATH"),
    Detection("codex", "cli", "Codex CLI", "on PATH"),
]
ONE_KEY = [Detection("openrouter", "api", "OpenRouter", "OPENROUTER_API_KEY")]


def always_ok(adapter_name, model, provider):
    return True, "OK"


def no_models(provider_type, base_url, api_key):
    return []


class QuickStartTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-setup-"))
        self.path = self.tempdir / "config.yaml"

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_quick_start_needs_one_keystroke_and_verifies_before_saving(self) -> None:
        io = ScriptedIO(answers=["1"])
        checked = []

        def verifier(adapter_name, model, provider):
            checked.append(adapter_name)
            return True, "OK"

        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=verifier)

        config = load_user_config(self.path)
        self.assertEqual("claude", config.roles["writer"].adapter)
        self.assertEqual("codex", config.roles["judge"].adapter)
        self.assertEqual(["claude", "codex"], checked)
        self.assertIn("OK", io.transcript)

    def test_menu_is_numbered_and_shows_what_was_detected(self) -> None:
        io = ScriptedIO(answers=["1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok)
        transcript = io.transcript
        self.assertIn("1)", transcript)
        self.assertIn("2)", transcript)
        self.assertIn("Claude Code", transcript)
        self.assertIn("on PATH", transcript)

    def test_a_failed_check_is_reported_and_nothing_is_saved(self) -> None:
        io = ScriptedIO(answers=["1"])

        def broken(adapter_name, model, provider):
            return False, "HTTP 401: no credit"

        result = run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=ONE_KEY, verifier=broken)

        self.assertIsNone(result)
        self.assertFalse(self.path.exists())
        self.assertIn("401", io.transcript)

    def test_single_provider_warns_that_it_will_judge_itself(self) -> None:
        io = ScriptedIO(answers=["1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=ONE_KEY, verifier=always_ok)
        self.assertIn("single family", io.transcript.lower())


class CustomSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-setup-"))
        self.path = self.tempdir / "config.yaml"

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_custom_picks_provider_by_number_and_asks_for_the_key_hidden(self) -> None:
        # 2 = custom; then writer provider by number, model, judge provider by number, model.
        io = ScriptedIO(answers=["2", "3", "anthropic/claude-sonnet-4.5", "4", "deepseek-chat"], secrets=["sk-or", "sk-ds"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models)

        config = load_user_config(self.path)
        self.assertIn("openrouter", config.providers)
        self.assertIn("deepseek", config.providers)
        self.assertEqual("openrouter", config.roles["writer"].adapter)
        self.assertEqual("anthropic/claude-sonnet-4.5", config.roles["writer"].model)
        self.assertEqual("deepseek", config.roles["judge"].adapter)
        self.assertNotIn("sk-or", io.transcript)
        self.assertNotIn("sk-ds", io.transcript)

    def test_blank_key_falls_back_to_the_environment_variable(self) -> None:
        # 2 = custom; 3 = openrouter; model; judge = last option (same as writing); judge model.
        io = ScriptedIO(answers=["2", "3", "some-model", "13", ""], secrets=[""])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models)
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("api_key_env: OPENROUTER_API_KEY", text)
        self.assertNotIn("api_key:", text)

    def test_models_are_offered_as_a_numbered_list_when_the_provider_lists_them(self) -> None:
        seen = []

        def lister(provider_type, base_url, api_key):
            seen.append((provider_type, base_url, api_key))
            return ["deepseek-chat", "deepseek-reasoner"]

        # 2 = custom; 4 = deepseek; model 2 = deepseek-reasoner; judge 13 = same; judge model 1.
        io = ScriptedIO(answers=["2", "4", "2", "13", "1"], secrets=["sk-ds"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=lister)

        config = load_user_config(self.path)
        self.assertEqual("deepseek-reasoner", config.roles["writer"].model)
        self.assertEqual("deepseek-chat", config.roles["judge"].model)
        self.assertEqual(("openai", "https://api.deepseek.com/v1", "sk-ds"), seen[0])
        self.assertIn("deepseek-reasoner", io.transcript)
        self.assertNotIn("sk-ds", io.transcript)

    def test_claude_models_come_from_a_fixed_list_and_oauth_help_is_shown_when_missing(self) -> None:
        # 2 = custom; 1 = claude (not detected -> OAuth help); model 2 = sonnet; judge 13 = same; judge model 1.
        io = ScriptedIO(answers=["2", "1", "2", "13", "1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models)
        config = load_user_config(self.path)
        self.assertEqual("sonnet", config.roles["writer"].model)
        self.assertIn("OAuth", io.transcript)
        self.assertIn("npm install -g @anthropic-ai/claude-code", io.transcript)


class ReRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-setup-"))
        self.path = self.tempdir / "config.yaml"

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_existing_config_offers_keep_change_reset_and_keep_changes_nothing(self) -> None:
        first = ScriptedIO(answers=["1"])
        run_setup(ask=first.ask, secret=first.secret, say=first.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok)
        before = self.path.read_text(encoding="utf-8")

        again = ScriptedIO(answers=["1"])  # 1 = keep
        run_setup(ask=again.ask, secret=again.secret, say=again.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok)

        self.assertEqual(before, self.path.read_text(encoding="utf-8"))
        transcript = again.transcript.lower()
        self.assertIn("keep", transcript)
        self.assertIn("reset", transcript)


if __name__ == "__main__":
    unittest.main()
