from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.onboarding import (  # type: ignore  # noqa: E402
    Detection,
    detect_environment,
    quick_plan,
    verify_candidate,
)


class DetectEnvironmentTests(unittest.TestCase):
    def test_finds_installed_clis(self) -> None:
        found = detect_environment(available={"claude": True, "codex": False}, env={}, probe=lambda url: False)
        keys = [detection.key for detection in found]
        self.assertIn("claude", keys)
        self.assertNotIn("codex", keys)
        self.assertEqual("cli", found[0].kind)
        self.assertIn("PATH", found[0].detail)

    def test_finds_api_keys_already_in_the_environment(self) -> None:
        found = detect_environment(
            available={"claude": False, "codex": False},
            env={"OPENROUTER_API_KEY": "sk-or-x", "DEEPSEEK_API_KEY": "sk-ds-x", "UNRELATED": "1"},
            probe=lambda url: False,
        )
        keys = {detection.key for detection in found}
        self.assertEqual({"openrouter", "deepseek"}, keys)
        openrouter = next(d for d in found if d.key == "openrouter")
        self.assertEqual("api", openrouter.kind)
        self.assertIn("OPENROUTER_API_KEY", openrouter.detail)
        self.assertNotIn("sk-or-x", openrouter.detail)

    def test_finds_local_servers_that_answer(self) -> None:
        found = detect_environment(
            available={"claude": False, "codex": False},
            env={},
            probe=lambda url: "11434" in url,
        )
        keys = [detection.key for detection in found]
        self.assertEqual(["ollama"], keys)
        self.assertEqual("local", found[0].kind)

    def test_clis_come_before_api_keys_before_local_servers(self) -> None:
        found = detect_environment(
            available={"claude": True, "codex": True},
            env={"OPENAI_API_KEY": "sk-x"},
            probe=lambda url: "11434" in url,
        )
        self.assertEqual(["cli", "cli", "api", "local"], [detection.kind for detection in found])

    def test_nothing_installed_is_an_empty_list_not_an_error(self) -> None:
        self.assertEqual([], detect_environment(available={"claude": False, "codex": False}, env={}, probe=lambda url: False))


class QuickPlanTests(unittest.TestCase):
    def test_two_families_split_writing_and_judging(self) -> None:
        found = [
            Detection("claude", "cli", "Claude Code", "on PATH"),
            Detection("codex", "cli", "Codex CLI", "on PATH"),
        ]
        plan = quick_plan(found)
        self.assertEqual("claude", plan.writer.key)
        self.assertEqual("codex", plan.judge.key)
        self.assertFalse(plan.single_family)

    def test_one_provider_judges_itself_and_says_so(self) -> None:
        found = [Detection("openrouter", "api", "OpenRouter", "OPENROUTER_API_KEY")]
        plan = quick_plan(found)
        self.assertEqual("openrouter", plan.writer.key)
        self.assertEqual("openrouter", plan.judge.key)
        self.assertTrue(plan.single_family)

    def test_nothing_detected_has_no_plan(self) -> None:
        self.assertIsNone(quick_plan([]))


class VerifyCandidateTests(unittest.TestCase):
    def test_a_working_provider_reports_ok(self) -> None:
        class Working:
            def complete(self, prompt, *, model=""):
                return "OK"

        ok, message = verify_candidate(Working(), "some-model")
        self.assertTrue(ok)
        self.assertIn("OK", message)

    def test_a_failing_provider_reports_why_without_the_key(self) -> None:
        from runner.adapters import AdapterError

        class Broken:
            def complete(self, prompt, *, model=""):
                raise AdapterError("openrouter returned HTTP 401: {'error': 'no credit'}")

        ok, message = verify_candidate(Broken(), "some-model")
        self.assertFalse(ok)
        self.assertIn("401", message)

    def test_an_empty_reply_is_a_failure(self) -> None:
        class Silent:
            def complete(self, prompt, *, model=""):
                return "   "

        ok, _ = verify_candidate(Silent(), "some-model")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
