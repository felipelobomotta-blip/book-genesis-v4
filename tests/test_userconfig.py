import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import AdapterError, AnthropicAdapter, OpenAICompatibleAdapter  # type: ignore  # noqa: E402
from runner.roles import build_role_adapters, plan_roles  # type: ignore  # noqa: E402
from runner.userconfig import UserConfig, load_user_config, write_user_config  # type: ignore  # noqa: E402


USER_CONFIG = """# written by book-genesis setup
provider_openrouter:
  type: openai
  base_url: https://openrouter.ai/api/v1
  api_key_env: BG_TEST_OPENROUTER_KEY

provider_deepseek:
  type: openai
  base_url: https://api.deepseek.com/v1
  api_key: sk-deepseek-in-file

writer:
  adapter: openrouter
  model: anthropic/claude-sonnet-4.5

judge:
  adapter: deepseek
  model: deepseek-chat

panel_1:
  adapter: deepseek
  model: deepseek-chat
  persona: the reader who buys this genre
"""


class UserConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-config-"))
        self.path = self.tempdir / "config.yaml"
        self.path.write_text(USER_CONFIG, encoding="utf-8")
        os.environ["BG_TEST_OPENROUTER_KEY"] = "sk-from-env"

    def tearDown(self) -> None:
        os.environ.pop("BG_TEST_OPENROUTER_KEY", None)
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_reads_providers_and_roles(self) -> None:
        config = load_user_config(self.path)
        self.assertEqual({"openrouter", "deepseek"}, set(config.providers))
        self.assertEqual("openai", config.providers["openrouter"].type)
        self.assertEqual("anthropic/claude-sonnet-4.5", config.roles["writer"].model)
        self.assertEqual(1, len(config.panel))

    def test_key_comes_from_env_or_file_and_missing_key_says_what_to_do(self) -> None:
        config = load_user_config(self.path)
        self.assertEqual("sk-from-env", config.providers["openrouter"].resolve_key())
        self.assertEqual("sk-deepseek-in-file", config.providers["deepseek"].resolve_key())
        os.environ.pop("BG_TEST_OPENROUTER_KEY")
        with self.assertRaises(AdapterError) as context:
            config.providers["openrouter"].resolve_key()
        self.assertIn("BG_TEST_OPENROUTER_KEY", str(context.exception))

    def test_user_roles_override_the_repository_defaults(self) -> None:
        config = load_user_config(self.path)
        plan = plan_roles(available={"claude": True, "codex": True}, user_config=config)
        self.assertEqual("openrouter", plan.roles["writer"].adapter)
        self.assertEqual("deepseek", plan.roles["judge"].adapter)
        self.assertEqual("claude", plan.roles["editor"].adapter)
        self.assertEqual(1, len(plan.panel))
        self.assertEqual([], plan.warnings)

    def test_build_role_adapters_instantiates_http_providers(self) -> None:
        config = load_user_config(self.path)
        setup = build_role_adapters(available={"claude": True, "codex": True}, user_config=config)
        self.assertIsInstance(setup.adapters["writer"], OpenAICompatibleAdapter)
        self.assertIsInstance(setup.adapters["judge"], OpenAICompatibleAdapter)
        self.assertEqual("anthropic/claude-sonnet-4.5", setup.models["writer"])

    def test_missing_file_means_no_user_config(self) -> None:
        self.assertIsNone(load_user_config(self.tempdir / "absent.yaml"))

    def test_write_and_reload_round_trip_keeps_the_key_out_of_the_summary(self) -> None:
        config = UserConfig.from_choices(
            providers={"anthropic": {"type": "anthropic", "base_url": "https://api.anthropic.com", "api_key": "sk-ant-secret"}},
            roles={"writer": ("anthropic", "claude-opus-4-1"), "judge": ("codex", "")},
        )
        write_user_config(config, self.path)
        reloaded = load_user_config(self.path)
        self.assertEqual("sk-ant-secret", reloaded.providers["anthropic"].resolve_key())
        self.assertIsInstance(build_role_adapters(available={"codex": True, "claude": False}, user_config=reloaded).adapters["writer"], AnthropicAdapter)
        self.assertNotIn("sk-ant-secret", reloaded.summary())


if __name__ == "__main__":
    unittest.main()
