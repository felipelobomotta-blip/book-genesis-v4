"""Find what this machine can already run, and prove it works before anything is saved.

Modelled on how OpenClaw, Hermes and opencode onboard: a read-only detection pass over
installed CLIs, API-key environment variables and reachable local servers, then a real
completion against the candidate. A configuration that was never called is a guess.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Callable, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

from runner.adapters import Adapter, AdapterError

PROBE_PROMPT = "Reply with exactly the word OK and nothing else."
PROBE_TIMEOUT_SECONDS = 3

CLI_LABELS = {"claude": "Claude Code", "codex": "Codex CLI"}

# Environment variable -> provider key. Order decides which one is offered first.
ENV_KEYS: Dict[str, str] = {
    "OPENROUTER_API_KEY": "openrouter",
    "ANTHROPIC_API_KEY": "anthropic",
    "OPENAI_API_KEY": "openai",
    "DEEPSEEK_API_KEY": "deepseek",
    "GROQ_API_KEY": "groq",
    "TOGETHER_API_KEY": "together",
}

LOCAL_SERVERS = {
    "ollama": "http://localhost:11434/v1",
    "lmstudio": "http://localhost:1234/v1",
}

API_LABELS = {
    "openrouter": "OpenRouter",
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "deepseek": "DeepSeek",
    "groq": "Groq",
    "together": "Together",
    "ollama": "Ollama (local)",
    "lmstudio": "LM Studio (local)",
}

KIND_ORDER = {"cli": 0, "api": 1, "local": 2}


@dataclass(frozen=True)
class Detection:
    key: str
    kind: str  # cli | api | local
    label: str
    detail: str  # where it came from; never the key itself

    def line(self) -> str:
        return f"{self.label} ({self.detail})"


@dataclass(frozen=True)
class QuickPlan:
    writer: Detection
    judge: Detection

    @property
    def single_family(self) -> bool:
        return self.writer.key == self.judge.key


def detect_environment(
    available: Optional[Dict[str, bool]] = None,
    env: Optional[Dict[str, str]] = None,
    probe: Optional[Callable[[str], bool]] = None,
) -> List[Detection]:
    """Read-only pass. Nothing is called, nothing is written; local servers get a HEAD-ish GET."""
    if available is None:
        from runner.roles import available_adapters

        available = available_adapters()
    env = os.environ if env is None else env
    probe = probe or _server_answers

    found: List[Detection] = []
    for name, label in CLI_LABELS.items():
        if available.get(name):
            found.append(Detection(name, "cli", label, "on PATH, already logged in"))
    for variable, key in ENV_KEYS.items():
        if env.get(variable):
            found.append(Detection(key, "api", API_LABELS[key], f"key in {variable}"))
    for key, base_url in LOCAL_SERVERS.items():
        if probe(base_url):
            found.append(Detection(key, "local", API_LABELS[key], f"answering at {base_url}"))
    found.sort(key=lambda detection: KIND_ORDER[detection.kind])
    return found


def quick_plan(detections: List[Detection]) -> Optional[QuickPlan]:
    """Writer takes the first detection; the judge takes the first one from another provider."""
    if not detections:
        return None
    writer = detections[0]
    judge = next((detection for detection in detections[1:] if detection.key != writer.key), writer)
    return QuickPlan(writer=writer, judge=judge)


def verify_candidate(adapter: Adapter, model: str) -> Tuple[bool, str]:
    """One real completion. Returns (ok, message); the message never carries a key."""
    try:
        reply = adapter.complete(PROBE_PROMPT, model=model)
    except AdapterError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001 - a broken provider must not crash onboarding
        return False, f"{type(exc).__name__}: {exc}"
    text = (reply or "").strip()
    if not text:
        return False, "the provider answered with nothing"
    return True, f"answered {text.splitlines()[0][:40]!r}"


def list_models(
    provider_type: str,
    base_url: str,
    api_key: str,
    fetch: Optional[Callable[[str, Dict[str, str]], Tuple[int, bytes]]] = None,
) -> List[str]:
    """Live model ids from the provider, like Hermes' model picker. Empty on any failure."""
    import json

    fetch = fetch or _http_get
    base = base_url.rstrip("/")
    if provider_type == "anthropic":
        url = f"{base}/v1/models"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    else:
        url = f"{base}/models"
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        status, raw = fetch(url, headers)
        if status != 200:
            return []
        data = json.loads(raw.decode("utf-8"))
        items = data.get("data", data if isinstance(data, list) else [])
        ids = [str(item.get("id", "")) for item in items if isinstance(item, dict) and item.get("id")]
    except Exception:  # noqa: BLE001 - listing is a convenience, never a blocker
        return []
    return sorted(dict.fromkeys(ids))


def _http_get(url: str, headers: Dict[str, str]) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def _server_answers(base_url: str) -> bool:
    request = urllib.request.Request(f"{base_url.rstrip('/')}/models", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=PROBE_TIMEOUT_SECONDS) as response:
            return 200 <= response.status < 500
    except (urllib.error.URLError, OSError, ValueError):
        return False
