from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

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

    def say(self, text: str) -> None:
        self.shown.append(text)


class SetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-setup-"))
        self.path = self.tempdir / "config.yaml"

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_openrouter_for_writing_and_deepseek_for_judging(self) -> None:
        io = ScriptedIO(
            answers=[
                "openrouter",                    # main provider
                "",                              # base url: keep default
                "anthropic/claude-sonnet-4.5",   # writer model
                "deepseek",                      # judge provider
                "",                              # base url default
                "deepseek-chat",                 # judge model
            ],
            secrets=["sk-or-secret", "sk-ds-secret"],
        )
        config_path = run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, available={"claude": False, "codex": False})

        config = load_user_config(config_path)
        self.assertEqual("openai", config.providers["openrouter"].type)
        self.assertEqual("https://openrouter.ai/api/v1", config.providers["openrouter"].base_url)
        self.assertEqual("sk-or-secret", config.providers["openrouter"].resolve_key())
        self.assertEqual("openrouter", config.roles["writer"].adapter)
        self.assertEqual("anthropic/claude-sonnet-4.5", config.roles["writer"].model)
        self.assertEqual("openrouter", config.roles["editor"].adapter)
        self.assertEqual("deepseek", config.roles["judge"].adapter)
        self.assertEqual("deepseek-chat", config.roles["judge"].model)
        self.assertTrue(all(seat.adapter == "deepseek" for seat in config.panel))
        shown = "\n".join(io.shown)
        self.assertNotIn("sk-or-secret", shown)
        self.assertNotIn("sk-ds-secret", shown)

    def test_installed_cli_needs_no_key_and_judge_defaults_to_the_other_family(self) -> None:
        io = ScriptedIO(answers=["claude", "", "", "", ""])
        config_path = run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, available={"claude": True, "codex": True})

        config = load_user_config(config_path)
        self.assertEqual("claude", config.roles["writer"].adapter)
        self.assertEqual("codex", config.roles["judge"].adapter)
        self.assertEqual({}, config.providers)

    def test_blank_key_means_environment_variable(self) -> None:
        io = ScriptedIO(answers=["deepseek", "", "", "same", "", ""], secrets=["", ""])
        config_path = run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, available={"claude": False, "codex": False})
        text = config_path.read_text(encoding="utf-8")
        self.assertIn("api_key_env: DEEPSEEK_API_KEY", text)
        self.assertNotIn("api_key:", text)


if __name__ == "__main__":
    unittest.main()
