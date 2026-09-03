import json
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.onboarding import list_models  # type: ignore  # noqa: E402


class ListModelsTests(unittest.TestCase):
    def test_openai_compatible_listing(self) -> None:
        calls = []

        def fetch(url, headers):
            calls.append((url, headers))
            return 200, json.dumps({"data": [{"id": "b-model"}, {"id": "a-model"}, {"id": "a-model"}]}).encode("utf-8")

        models = list_models("openai", "https://api.deepseek.com/v1/", "sk-x", fetch=fetch)
        self.assertEqual(["a-model", "b-model"], models)
        self.assertEqual("https://api.deepseek.com/v1/models", calls[0][0])
        self.assertEqual("Bearer sk-x", calls[0][1]["Authorization"])

    def test_anthropic_listing_uses_its_own_headers(self) -> None:
        calls = []

        def fetch(url, headers):
            calls.append((url, headers))
            return 200, json.dumps({"data": [{"id": "claude-sonnet-5"}]}).encode("utf-8")

        models = list_models("anthropic", "https://api.anthropic.com", "sk-ant", fetch=fetch)
        self.assertEqual(["claude-sonnet-5"], models)
        self.assertEqual("https://api.anthropic.com/v1/models", calls[0][0])
        self.assertEqual("sk-ant", calls[0][1]["x-api-key"])

    def test_failures_return_an_empty_list(self) -> None:
        self.assertEqual([], list_models("openai", "https://x", "k", fetch=lambda url, headers: (401, b"{}")))
        self.assertEqual([], list_models("openai", "https://x", "k", fetch=lambda url, headers: (200, b"not json")))

        def boom(url, headers):
            raise OSError("no network")

        self.assertEqual([], list_models("openai", "https://x", "k", fetch=boom))


if __name__ == "__main__":
    unittest.main()
