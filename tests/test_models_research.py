"""Models are never a static list: live for API providers, probed for the CLIs, cached."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.onboarding import (  # type: ignore  # noqa: E402
    cached_models,
    chat_models_only,
    probe_models,
    sort_models,
    store_models,
)


class ChatModelsOnlyTests(unittest.TestCase):
    def test_drops_what_a_book_pipeline_cannot_use(self) -> None:
        raw = [
            "gpt-5.5", "gpt-5.5-pro", "text-embedding-3-small", "tts-1", "whisper-1", "dall-e-3",
            "gpt-5-image", "gpt-audio", "omni-moderation-latest", "gpt-realtime-2.1", "gpt-5.6-cyber",
        ]
        self.assertEqual(["gpt-5.5", "gpt-5.5-pro"], chat_models_only(raw))

    def test_drops_provider_variants_and_dated_snapshots_with_an_undated_twin(self) -> None:
        raw = ["gpt-4o", "gpt-4o-2024-08-06", "gpt-4o:batch", "claude-haiku-4-5-20251001", "anthropic/claude-opus-5:batch"]
        self.assertEqual(["gpt-4o", "claude-haiku-4-5-20251001", "anthropic/claude-opus-5"], chat_models_only(raw))

    def test_gemini_is_not_a_mini_and_gemma_stays(self) -> None:
        raw = ["gemini-3.1-pro-preview", "gemini-3.8-flash", "gemma-4-31b-it", "gemini-3.1-flash-image"]
        self.assertEqual(["gemini-3.8-flash", "gemma-4-31b-it"], chat_models_only(raw))


class SortModelsTests(unittest.TestCase):
    def test_newest_version_first(self) -> None:
        self.assertEqual(
            ["gpt-5.6-sol", "gpt-5.5", "gpt-5.5-pro", "gpt-5.4", "gpt-5", "gpt-4.1", "o3"],  # base before its variants
            sort_models(["gpt-4.1", "gpt-5", "o3", "gpt-5.5", "gpt-5.6-sol", "gpt-5.4", "gpt-5.5-pro"]),
        )

    def test_claude_generations_in_order(self) -> None:
        self.assertEqual(
            ["claude-opus-5", "claude-sonnet-5", "claude-opus-4-8", "claude-opus-4-7", "claude-haiku-4-5-20251001", "claude-sonnet-4-5"],
            sort_models(["claude-sonnet-4-5", "claude-opus-4-7", "claude-opus-5", "claude-haiku-4-5-20251001", "claude-opus-4-8", "claude-sonnet-5"]),
        )


class FakeCli:
    """Accepts a fixed set of ids; everything else fails, like a real subscription CLI."""

    name = "fake-cli"

    def __init__(self, accepted):
        self.accepted = set(accepted)
        self.calls = []

    def complete(self, prompt, *, model=""):
        from runner.adapters import AdapterError

        self.calls.append(model)
        if model in self.accepted:
            return "OK"
        raise AdapterError(f"{self.name} exited 1: unknown model {model}")


class ProbeModelsTests(unittest.TestCase):
    def test_keeps_only_the_ids_that_answered_in_candidate_order(self) -> None:
        cli = FakeCli({"gpt-5.5", "gpt-5.4"})
        seen = []
        accepted = probe_models(cli, ["gpt-5.5", "gpt-5.5-mini", "gpt-5.4", "o3"], workers=2, on_result=lambda c, ok: seen.append((c, ok)))
        self.assertEqual(["gpt-5.5", "gpt-5.4"], accepted)
        self.assertEqual(4, len(cli.calls))
        self.assertEqual({("gpt-5.5", True), ("gpt-5.5-mini", False), ("gpt-5.4", True), ("o3", False)}, set(seen))


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="book-genesis-cache-"))
        self.path = self.tempdir / "models-cache.json"

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_round_trip_and_expiry(self) -> None:
        self.assertIsNone(cached_models("codex", self.path))
        store_models("codex", ["gpt-5.5", "gpt-5.4"], self.path, now=1_000_000.0)
        self.assertEqual(["gpt-5.5", "gpt-5.4"], cached_models("codex", self.path, now=1_000_000.0 + 3600))
        self.assertIsNone(cached_models("codex", self.path, now=1_000_000.0 + 8 * 24 * 3600))
        self.assertIsNone(cached_models("claude", self.path, now=1_000_000.0))

    def test_keys_do_not_overwrite_each_other(self) -> None:
        store_models("codex", ["gpt-5.5"], self.path, now=5.0)
        store_models("claude", ["claude-opus-5"], self.path, now=5.0)
        self.assertEqual(["gpt-5.5"], cached_models("codex", self.path, now=6.0))
        self.assertEqual(["claude-opus-5"], cached_models("claude", self.path, now=6.0))


if __name__ == "__main__":
    unittest.main()
