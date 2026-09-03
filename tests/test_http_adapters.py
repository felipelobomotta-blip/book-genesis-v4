import json
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from runner.adapters import AdapterError, AnthropicAdapter, OpenAICompatibleAdapter  # type: ignore  # noqa: E402


class FakeTransport:
    """Records the request and returns a canned (status, body)."""

    def __init__(self, status: int, body: dict) -> None:
        self.status = status
        self.body = json.dumps(body).encode("utf-8")
        self.requests = []

    def __call__(self, url, headers, body, timeout_seconds):
        self.requests.append({"url": url, "headers": headers, "body": json.loads(body.decode("utf-8"))})
        return self.status, self.body


class OpenAICompatibleAdapterTests(unittest.TestCase):
    def test_posts_chat_completion_and_reads_the_reply(self) -> None:
        transport = FakeTransport(200, {"choices": [{"message": {"role": "assistant", "content": "# Chapter 1\n\nText."}}]})
        adapter = OpenAICompatibleAdapter("openrouter", "https://openrouter.ai/api/v1", "sk-secret", transport=transport)

        text = adapter.complete("write it", model="deepseek/deepseek-chat")

        self.assertEqual("# Chapter 1\n\nText.", text)
        request = transport.requests[0]
        self.assertEqual("https://openrouter.ai/api/v1/chat/completions", request["url"])
        self.assertEqual("Bearer sk-secret", request["headers"]["Authorization"])
        self.assertEqual("deepseek/deepseek-chat", request["body"]["model"])
        self.assertEqual("write it", request["body"]["messages"][0]["content"])

    def test_http_error_never_echoes_the_key(self) -> None:
        transport = FakeTransport(401, {"error": {"message": "invalid key"}})
        adapter = OpenAICompatibleAdapter("openrouter", "https://openrouter.ai/api/v1", "sk-secret", transport=transport)
        with self.assertRaises(AdapterError) as context:
            adapter.complete("write it", model="x")
        message = str(context.exception)
        self.assertIn("401", message)
        self.assertNotIn("sk-secret", message)

    def test_model_is_required(self) -> None:
        adapter = OpenAICompatibleAdapter("openrouter", "https://openrouter.ai/api/v1", "sk-secret", transport=FakeTransport(200, {}))
        with self.assertRaises(AdapterError):
            adapter.complete("write it", model="")


class AnthropicAdapterTests(unittest.TestCase):
    def test_posts_messages_and_reads_the_text_block(self) -> None:
        transport = FakeTransport(200, {"content": [{"type": "text", "text": "Reply text."}]})
        adapter = AnthropicAdapter("anthropic", "https://api.anthropic.com", "sk-ant-secret", transport=transport)

        text = adapter.complete("judge it", model="claude-sonnet-4-5")

        self.assertEqual("Reply text.", text)
        request = transport.requests[0]
        self.assertEqual("https://api.anthropic.com/v1/messages", request["url"])
        self.assertEqual("sk-ant-secret", request["headers"]["x-api-key"])
        self.assertIn("anthropic-version", request["headers"])
        self.assertEqual("claude-sonnet-4-5", request["body"]["model"])
        self.assertGreaterEqual(request["body"]["max_tokens"], 8000)


if __name__ == "__main__":
    unittest.main()
