from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.onboarding import Detection  # type: ignore  # noqa: E402
from runner.setup import run_setup, tag_model  # type: ignore  # noqa: E402
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

# What the probe found on the machine this was written on (2026-09-03): Claude Code took the
# Claude 5 ids and the aliases but not fable; Codex took gpt-5.5 and gpt-5.4 and nothing else.
PROBED = {
    "claude": ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5-20251001", "opus", "sonnet", "haiku"],
    "codex": ["gpt-5.5", "gpt-5.4"],
}


def always_ok(adapter_name, model, provider):
    return True, "OK"


def no_models(provider_type, base_url, api_key):
    return []


def probed(key):
    return list(PROBED.get(key, []))


def nothing_probed(key):
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
            checked.append((adapter_name, model))
            return True, "OK"

        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=verifier, prober=probed)

        config = load_user_config(self.path)
        self.assertEqual("claude", config.roles["writer"].adapter)
        self.assertEqual("codex", config.roles["judge"].adapter)
        self.assertEqual([("claude", "claude-opus-5"), ("codex", "gpt-5.5")], checked)
        self.assertIn("OK", io.transcript)

    def test_quick_start_defaults_follow_the_providers_own_docs(self) -> None:
        io = ScriptedIO(answers=["1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok, prober=probed)
        config = load_user_config(self.path)
        self.assertEqual("claude-opus-5", config.roles["writer"].model)
        self.assertEqual("claude-opus-5", config.roles["editor"].model)
        self.assertEqual("claude-sonnet-5", config.roles["disruptor"].model)
        self.assertEqual("claude-haiku-4-5-20251001", config.roles["extractor"].model)
        self.assertEqual("gpt-5.5", config.roles["judge"].model)

    def test_quick_start_with_two_families_mixes_the_panel(self) -> None:
        io = ScriptedIO(answers=["1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok, prober=probed)
        config = load_user_config(self.path)
        adapters = {seat.adapter for seat in config.panel}
        self.assertEqual({"claude", "codex"}, adapters)
        self.assertEqual(3, len(config.panel))

    def test_menu_is_numbered_and_shows_what_was_detected(self) -> None:
        io = ScriptedIO(answers=["1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok, prober=probed)
        transcript = io.transcript
        self.assertIn("1)", transcript)
        self.assertIn("2)", transcript)
        self.assertIn("Claude Code", transcript)
        self.assertIn("on PATH", transcript)

    def test_a_failed_check_is_reported_and_nothing_is_saved(self) -> None:
        io = ScriptedIO(answers=["1"])

        def broken(adapter_name, model, provider):
            return False, "HTTP 401: no credit"

        result = run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=ONE_KEY, verifier=broken, prober=probed)

        self.assertIsNone(result)
        self.assertFalse(self.path.exists())
        self.assertIn("401", io.transcript)

    def test_single_provider_warns_that_it_will_judge_itself(self) -> None:
        io = ScriptedIO(answers=["1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=ONE_KEY, verifier=always_ok, prober=probed)
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
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models, prober=probed)

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
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models, prober=probed)
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("api_key_env: OPENROUTER_API_KEY", text)
        self.assertNotIn("api_key:", text)

    def test_api_models_come_live_filtered_and_newest_first(self) -> None:
        seen = []

        def lister(provider_type, base_url, api_key):
            seen.append((provider_type, base_url, api_key))
            return ["deepseek-chat", "deepseek-v3.2", "deepseek-v4-pro", "deepseek-v4-flash-vision-exp", "deepseek-chat:batch"]

        # 2 = custom; 4 = deepseek; writer model 2; judge 13 = same; judge model 1.
        io = ScriptedIO(answers=["2", "4", "2", "13", "1"], secrets=["sk-ds"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=lister, prober=probed)

        transcript = io.transcript
        # recommended first, then newest first; the vision-exp and :batch variants are gone
        self.assertIn("1) deepseek-chat  (best cost/quality balance, recommended)", transcript)
        self.assertIn("2) deepseek-v4-pro  (pricier, the strongest for writing a book)", transcript)
        self.assertIn("3) deepseek-v3.2  (best cost/quality balance)", transcript)
        self.assertNotIn("vision-exp", transcript)
        self.assertNotIn(":batch", transcript)
        config = load_user_config(self.path)
        self.assertEqual("deepseek-v4-pro", config.roles["writer"].model)  # the raw id, not the label
        self.assertEqual("deepseek-chat", config.roles["judge"].model)
        self.assertEqual(("openai", "https://api.deepseek.com/v1", "sk-ds"), seen[0])
        self.assertNotIn("sk-ds", transcript)

    def test_claude_models_are_the_probed_ids_with_versions_and_oauth_help_when_missing(self) -> None:
        # 2 = custom; 1 = claude (not detected -> OAuth help); writer model 2; judge 13 = same; judge model 1.
        io = ScriptedIO(answers=["2", "1", "2", "13", "1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models, prober=probed)
        transcript = io.transcript
        self.assertIn("1) claude-opus-5  (pricier, the strongest for writing a book, recommended)", transcript)
        self.assertIn("2) claude-sonnet-5  (best cost/quality balance)", transcript)
        self.assertIn("claude-haiku-4-5-20251001  (cheaper, fine for mechanical roles)", transcript)
        self.assertIn("opus  (alias: always the newest Opus)", transcript)
        self.assertNotIn("claude-fable-5-1", transcript)  # the probe said no
        config = load_user_config(self.path)
        self.assertEqual("claude-sonnet-5", config.roles["writer"].model)
        self.assertIn("OAuth", transcript)
        self.assertIn("npm install -g @anthropic-ai/claude-code", transcript)

    def test_codex_models_are_the_probed_ids_not_a_blank_prompt(self) -> None:
        # 2 = custom; 2 = codex; writer model 1; judge 13 = same; judge model 2.
        io = ScriptedIO(answers=["2", "2", "1", "13", "2"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models, prober=probed)
        transcript = io.transcript
        self.assertIn("1) gpt-5.5  (best cost/quality balance, recommended)", transcript)
        self.assertIn("2) gpt-5.4  (best cost/quality balance)", transcript)
        self.assertNotIn("gpt-5.5-mini", transcript)
        config = load_user_config(self.path)
        self.assertEqual("gpt-5.5", config.roles["writer"].model)
        self.assertEqual("gpt-5.4", config.roles["judge"].model)

    def test_a_cli_that_probes_nothing_still_offers_the_aliases(self) -> None:
        io = ScriptedIO(answers=["2", "1", "1", "13", "1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models, prober=nothing_probed)
        transcript = io.transcript
        self.assertIn("opus  (alias: always the newest Opus)", transcript)
        self.assertIn("Type another model id", transcript)

    def test_each_role_gets_one_line_of_guidance_before_the_list(self) -> None:
        io = ScriptedIO(answers=["2", "1", "1", "13", "1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=[], verifier=always_ok, lister=no_models, prober=probed)
        transcript = io.transcript
        self.assertIn("The writer is where the prose comes from", transcript)
        self.assertIn("The judge only reads and answers", transcript)


class TagTests(unittest.TestCase):
    def test_tags_follow_the_naming_every_provider_shares(self) -> None:
        self.assertIn("strongest", tag_model("claude-opus-5"))
        self.assertIn("strongest", tag_model("claude-fable-5-1"))
        self.assertIn("strongest", tag_model("gemini-3.1-pro-high"))
        self.assertIn("strongest", tag_model("gpt-5.5-pro"))
        self.assertIn("strongest", tag_model("gpt-5.6-sol"))
        self.assertIn("strongest", tag_model("o3"))
        self.assertIn("strongest", tag_model("deepseek-reasoner"))
        self.assertIn("cheaper", tag_model("claude-haiku-4-5-20251001"))
        self.assertIn("cheaper", tag_model("gpt-5.4-mini"))
        self.assertIn("cheaper", tag_model("gpt-5.6-luna"))
        self.assertIn("cheaper", tag_model("gemini-3.8-flash-high"))
        self.assertIn("cheaper", tag_model("o3-mini"))  # budget wins over the o-series hint
        self.assertIn("balance", tag_model("claude-sonnet-5"))
        self.assertIn("balance", tag_model("gpt-5.5"))
        self.assertIn("balance", tag_model("gpt-5.6-terra"))
        self.assertIn("balance", tag_model("deepseek-chat"))


class ReRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-setup-"))
        self.path = self.tempdir / "config.yaml"

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_existing_config_offers_keep_change_reset_and_keep_changes_nothing(self) -> None:
        first = ScriptedIO(answers=["1"])
        run_setup(ask=first.ask, secret=first.secret, say=first.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok, prober=probed)
        before = self.path.read_text(encoding="utf-8")

        again = ScriptedIO(answers=["1"])  # 1 = keep
        run_setup(ask=again.ask, secret=again.secret, say=again.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok, prober=probed)

        self.assertEqual(before, self.path.read_text(encoding="utf-8"))
        transcript = again.transcript.lower()
        self.assertIn("keep", transcript)
        self.assertIn("reset", transcript)

    def test_change_keeps_the_stored_providers_and_keys(self) -> None:
        # Bug seen 2026-09-03: a re-run rebuilt the config from scratch and the person's
        # OpenAI and DeepSeek keys, typed once, vanished from the file.
        self.path.write_text(
            "provider_openai:\n  type: openai\n  base_url: https://api.openai.com/v1\n  api_key: sk-openai-stored\n"
            "provider_deepseek:\n  type: openai\n  base_url: https://api.deepseek.com/v1\n  api_key_env: DEEPSEEK_API_KEY\n"
            "writer:\n  adapter: openai\n  model: gpt-5.5\n"
            "judge:\n  adapter: deepseek\n  model: deepseek-chat\n",
            encoding="utf-8",
        )
        # 2 = change; 1 = quick start (claude writes, codex judges).
        io = ScriptedIO(answers=["2", "1"])
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok, prober=probed)

        config = load_user_config(self.path)
        self.assertEqual("claude", config.roles["writer"].adapter)
        self.assertEqual("sk-openai-stored", config.providers["openai"].api_key)
        self.assertEqual("DEEPSEEK_API_KEY", config.providers["deepseek"].api_key_env)
        self.assertIn("Keeping stored providers: openai, deepseek", io.transcript)
        self.assertNotIn("sk-openai-stored", io.transcript)

    def test_reset_drops_the_stored_providers_and_says_so(self) -> None:
        self.path.write_text(
            "provider_openai:\n  type: openai\n  base_url: https://api.openai.com/v1\n  api_key: sk-openai-stored\n"
            "writer:\n  adapter: openai\n  model: gpt-5.5\n",
            encoding="utf-8",
        )
        io = ScriptedIO(answers=["3", "1"])  # 3 = reset; 1 = quick start
        run_setup(ask=io.ask, secret=io.secret, say=io.say, path=self.path, detections=BOTH_CLIS, verifier=always_ok, prober=probed)
        config = load_user_config(self.path)
        self.assertEqual({}, config.providers)
        self.assertIn("dropped", io.transcript.lower())


if __name__ == "__main__":
    unittest.main()
