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
    "GEMINI_API_KEY": "gemini-api",
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
    "gemini-api": "Gemini API",
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


import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Tokens that mark a model as not-a-chat-model (embeddings, speech, images, moderation,
# provider-specific variants). Whole tokens, so "gemini" never trips on "mini".
_NON_CHAT_TOKENS = {
    "embedding", "embeddings", "tts", "whisper", "dall", "dalle", "image", "audio", "realtime",
    "moderation", "transcribe", "transcription", "translate", "live", "search", "sora", "vision",
    "safeguard", "cyber", "instruct", "batch", "free", "davinci", "babbage", "curie", "ada", "lyria",
    "veo", "imagen", "banana", "robotics", "customtools",
}
_DATE_SUFFIX = re.compile(r"[-_](\d{4}-\d{2}-\d{2}|\d{8}|\d{4})$")
# Google ships flagships as "-preview" for months (gemini-3.1-pro-preview has no plain twin), so
# preview/exp ids stay unless the same id exists without the suffix.
_VARIANT_SUFFIX = re.compile(r"-(preview|exp)$")
_VERSION = re.compile(r"\d+(?:\.\d+)?")
CACHE_TTL_SECONDS = 7 * 24 * 3600
DEFAULT_CACHE_PATH = Path.home() / ".book-genesis" / "models-cache.json"


def _tokens(model_id: str) -> set:
    return {token for token in re.split(r"[^a-z0-9]+", model_id.lower()) if token}


def chat_models_only(ids: List[str]) -> List[str]:
    """Drop what a book pipeline can never use (embeddings, speech, images, moderation,
    provider variants like ':batch'), then drop dated snapshots that have an undated twin."""
    kept: List[str] = []
    for model_id in ids:
        base = model_id.split(":")[0]
        if _tokens(base) & _NON_CHAT_TOKENS:
            continue
        kept.append(base)
    kept = list(dict.fromkeys(kept))
    undated = set(kept)
    result: List[str] = []
    for model_id in kept:
        stripped = _VARIANT_SUFFIX.sub("", _DATE_SUFFIX.sub("", model_id))
        if stripped != model_id and stripped in undated:
            continue
        result.append(model_id)
    return result


def version_key(model_id: str):
    """Newest first: the first number in the id (5.5 before 5.4 before 5 before 4.1)."""
    numbers = _VERSION.findall(model_id.replace("-", ".").replace("_", "."))
    first = float(numbers[0]) if numbers else 0.0
    return (-first, model_id)


def sort_models(ids: List[str]) -> List[str]:
    return sorted(ids, key=version_key)


def probe_models(
    adapter: Adapter,
    candidates: List[str],
    *,
    workers: int = 4,
    on_result: Optional[Callable[[str, bool], None]] = None,
) -> List[str]:
    """One tiny real completion per candidate, in parallel; keeps the ones that answered.
    This is the only honest way to know what a subscription CLI accepts: the machine that ran
    this had a Codex CLI that took gpt-5.5 and gpt-5.4 and refused every other GPT id."""

    def one(candidate: str) -> Optional[str]:
        ok, _ = verify_candidate(adapter, candidate)
        if on_result is not None:
            on_result(candidate, ok)
        return candidate if ok else None

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(one, candidates))
    return [candidate for candidate in results if candidate]


def cached_models(key: str, path: Optional[Path] = None, *, ttl: int = CACHE_TTL_SECONDS, now: Optional[float] = None) -> Optional[List[str]]:
    target = path or DEFAULT_CACHE_PATH
    if not target.exists():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    entry = data.get(key) if isinstance(data, dict) else None
    if not isinstance(entry, dict):
        return None
    stamp = float(entry.get("at", 0))
    current = time.time() if now is None else now
    if current - stamp > ttl:
        return None
    models = entry.get("models")
    return list(models) if isinstance(models, list) else None


def store_models(key: str, models: List[str], path: Optional[Path] = None, *, now: Optional[float] = None) -> Path:
    target = path or DEFAULT_CACHE_PATH
    data: Dict[str, object] = {}
    if target.exists():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (ValueError, OSError):
            data = {}
    data[key] = {"at": time.time() if now is None else now, "models": list(models)}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return target


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
