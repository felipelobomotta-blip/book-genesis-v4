"""`book-genesis setup`: the onboarding wizard (ADR 0003, revised after ADR 0004).

Shaped like the onboarding of OpenClaw, Hermes and opencode: detect what the machine can
already run, offer a one-keystroke quick start, prove the choice with a real completion,
and only then write the config. Re-running is a verification pass, not a reset.

Every question goes through injectable ``ask`` / ``secret`` / ``say`` callables, so the whole
flow is testable with scripted answers and never touches the network in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from runner.onboarding import Detection, QuickPlan, detect_environment, list_models, quick_plan, verify_candidate
from runner.userconfig import UserConfig, load_user_config, user_config_path, write_user_config


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    type: str
    base_url: str
    key_env: str
    writer_model: str
    judge_model: str
    needs_key: bool = True


# The provider menu, in the order it is shown. The numbers are part of the interface.
MENU: List[Preset] = [
    Preset("claude", "Claude subscription (OAuth through the Claude Code CLI, no key)", "cli", "", "", "opus", "sonnet", needs_key=False),
    Preset("codex", "ChatGPT / Codex subscription (OAuth through the Codex CLI, no key)", "cli", "", "", "", "", needs_key=False),
    Preset("openrouter", "OpenRouter", "openai", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "anthropic/claude-sonnet-4.5", "deepseek/deepseek-chat"),
    Preset("deepseek", "DeepSeek", "openai", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", "deepseek-chat", "deepseek-chat"),
    Preset("anthropic", "Anthropic", "anthropic", "https://api.anthropic.com", "ANTHROPIC_API_KEY", "claude-sonnet-5", "claude-sonnet-5"),
    Preset("openai", "OpenAI", "openai", "https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-5.5", "gpt-5.5"),
    Preset("groq", "Groq", "openai", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile", "llama-3.3-70b-versatile"),
    Preset("together", "Together", "openai", "https://api.together.xyz/v1", "TOGETHER_API_KEY", "meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    Preset("ollama", "Ollama (local server)", "openai", "http://localhost:11434/v1", "", "llama3.1", "llama3.1", needs_key=False),
    Preset("lmstudio", "LM Studio (local server)", "openai", "http://localhost:1234/v1", "", "", "", needs_key=False),
    Preset("other", "Another OpenAI-compatible endpoint", "openai", "", "OTHER_API_KEY", "", ""),
    Preset("manual", "Nothing installed: paste every reply by hand", "manual", "", "", "", "", needs_key=False),
]
BY_KEY = {preset.key: preset for preset in MENU}
MAIN_ROLES = ("writer", "editor", "architect", "disruptor", "extractor")
CLI_MODELS = {"claude": ["opus", "sonnet", "haiku"], "codex": []}
OAUTH_HELP = {
    "claude": "Install Claude Code (`npm install -g @anthropic-ai/claude-code`), run `claude` once and log in; that login is the OAuth.",
    "codex": "Install the Codex CLI (`npm install -g @openai/codex`), run `codex login`; that login is the OAuth.",
}
MAX_MODELS_SHOWN = 15

Ask = Callable[..., str]
Secret = Callable[[str], str]
Say = Callable[..., None]
Verifier = Callable[[str, str, Optional[Dict[str, str]]], Tuple[bool, str]]
Lister = Callable[[str, str, str], List[str]]


def run_setup(
    *,
    ask: Ask,
    secret: Secret,
    say: Say,
    path: Optional[Path] = None,
    detections: Optional[List[Detection]] = None,
    verifier: Optional[Verifier] = None,
    available: Optional[Dict[str, bool]] = None,
    lister: Optional[Lister] = None,
) -> Optional[Path]:
    """Returns the config path, or None when the person skipped or a check failed."""
    target = user_config_path(path)
    check = verifier or _default_verifier
    models_of = lister or list_models
    found = detect_environment(available=available) if detections is None else list(detections)

    say("")
    say("Book Genesis setup")
    say("Nothing typed here leaves this machine. Keys are stored locally or read from your environment.")
    say("")

    if target.exists():
        existing = load_user_config(target)
        say(f"You already have a configuration at {target}:")
        if existing is not None:
            say(existing.summary())
        say("")
        choice = _menu(ask, say, "What do you want to do", ["Keep it as it is", "Change it", "Reset and start over"])
        if choice == 1:
            say("Kept. Run `book-genesis doctor` to check it, or `book-genesis new` to write a book.")
            return target
        if choice == 3:
            say("Starting over.")

    if found:
        say("Found on this machine:")
        for detection in found:
            say(f"  - {detection.line()}")
    else:
        say("No provider detected on this machine. You can connect one with a key.")
    say("")

    plan = quick_plan(found)
    options = [
        f"Quick start: {_plan_line(plan)}" if plan else "Quick start (nothing detected, not available)",
        "Custom: choose the provider and models myself",
        "Skip for now",
    ]
    choice = _menu(ask, say, "How do you want to run the models", options, default=1 if plan else 2)
    if choice == 3:
        say("Skipped. Run `book-genesis setup` whenever you want.")
        return None
    if choice == 1 and plan is not None:
        return _quick(plan, ask, secret, say, target, check)
    return _custom(ask, secret, say, target, check, found, models_of)


def _quick(plan: QuickPlan, ask: Ask, secret: Secret, say: Say, target: Path, check: Verifier) -> Optional[Path]:
    providers: Dict[str, Dict[str, str]] = {}
    say("")
    writer = _entry_for(plan.writer.key, "writing", providers, ask, secret, say, None, interactive=False)
    judge = writer if plan.single_family else _entry_for(plan.judge.key, "judging", providers, ask, secret, say, None, interactive=False)
    if plan.single_family:
        judge = (judge[0], BY_KEY[plan.judge.key].judge_model or judge[1])
        say("Note: single family. The same provider writes and judges, which is a weaker gate than two providers.")
        say("Connect a second provider later with `book-genesis setup` when you can.")
        say("")

    for label, (adapter_name, model) in (("writer", writer), ("judge", judge)):
        say(f"Checking {label}: {adapter_name}{' ' + model if model else ''} ...")
        ok, message = check(adapter_name, model, providers.get(adapter_name))
        if not ok:
            say(f"  failed: {message}")
            say("Nothing was saved. Fix the provider and run `book-genesis setup` again, or choose Custom.")
            return None
        say(f"  ok, {message}")

    return _save(providers, writer, judge, say, target)


def _custom(
    ask: Ask,
    secret: Secret,
    say: Say,
    target: Path,
    check: Verifier,
    found: List[Detection],
    models_of: Lister,
) -> Optional[Path]:
    providers: Dict[str, Dict[str, str]] = {}
    detected = {detection.key for detection in found}
    labels = [preset.label + (" [detected]" if preset.key in detected else "") for preset in MENU]

    say("")
    index = _menu(ask, say, "Provider for writing (writer, editor, architect)", labels, default=1)
    key = MENU[index - 1].key
    if key in OAUTH_HELP and key not in detected:
        say(f"  {OAUTH_HELP[key]}")
    writer = _entry_for(key, "writing", providers, ask, secret, say, models_of, interactive=True)

    say("")
    judge_labels = labels + ["Same as writing"]
    judge_index = _menu(ask, say, "Provider for judging (a different one is a stronger gate)", judge_labels, default=len(judge_labels))
    if judge_index == len(judge_labels):
        default_model = BY_KEY[writer[0]].judge_model if writer[0] in BY_KEY else writer[1]
        judge = (writer[0], _pick_model(writer[0], "judging", default_model, providers, ask, say, models_of) or writer[1])
    else:
        key = MENU[judge_index - 1].key
        if key in OAUTH_HELP and key not in detected:
            say(f"  {OAUTH_HELP[key]}")
        judge = _entry_for(key, "judging", providers, ask, secret, say, models_of, interactive=True)

    for label, (adapter_name, model) in (("writer", writer), ("judge", judge)):
        say(f"Checking {label}: {adapter_name}{' ' + model if model else ''} ...")
        ok, message = check(adapter_name, model, providers.get(adapter_name))
        if not ok:
            say(f"  failed: {message}")
            say("Nothing was saved. Run `book-genesis setup` again when the provider works.")
            return None
        say(f"  ok, {message}")

    if writer[0] == judge[0]:
        say("Note: single family. The same provider writes and judges, which is a weaker gate than two providers.")
    return _save(providers, writer, judge, say, target)


def _entry_for(
    key: str,
    purpose: str,
    providers: Dict[str, Dict[str, str]],
    ask: Ask,
    secret: Secret,
    say: Say,
    models_of: Optional[Lister],
    *,
    interactive: bool,
) -> Tuple[str, str]:
    preset = BY_KEY[key]
    default_model = preset.writer_model if purpose == "writing" else preset.judge_model
    if preset.type in ("cli", "manual"):
        if not interactive:
            return key, default_model
        return key, _pick_model(key, purpose, default_model, providers, ask, say, models_of)
    if key not in providers:
        base_url = preset.base_url or ask(f"Base URL for {key} (ends in /v1)", "")
        entry: Dict[str, str] = {"type": preset.type, "base_url": base_url}
        if preset.needs_key:
            typed = secret(f"API key for {key} (leave blank to read {preset.key_env} from your environment)")
            if typed:
                entry["api_key"] = typed
            else:
                entry["api_key_env"] = preset.key_env
        else:
            entry["api_key"] = "local"
        providers[key] = entry
    if not interactive:
        return key, default_model
    return key, _pick_model(key, purpose, default_model, providers, ask, say, models_of) or default_model


def _pick_model(
    key: str,
    purpose: str,
    default_model: str,
    providers: Dict[str, Dict[str, str]],
    ask: Ask,
    say: Say,
    models_of: Optional[Lister],
) -> str:
    """A numbered list of live models when the provider can list them; a typed answer otherwise."""
    candidates: List[str] = []
    if key in CLI_MODELS:
        candidates = list(CLI_MODELS[key])
    elif models_of is not None and key in providers:
        entry = providers[key]
        api_key = entry.get("api_key", "")
        if not api_key and entry.get("api_key_env"):
            import os

            api_key = os.environ.get(entry["api_key_env"], "")
        candidates = models_of(entry.get("type", "openai"), entry.get("base_url", ""), api_key)
    if not candidates:
        return ask(f"Model for {purpose} on {key}", default_model) or default_model
    shown = _prioritise(candidates, default_model)[:MAX_MODELS_SHOWN]
    options = shown + ["Type another model id"]
    default_index = shown.index(default_model) + 1 if default_model in shown else 1
    choice = _menu(ask, say, f"Model for {purpose} on {key}", options, default=default_index)
    if choice == len(options):
        return ask("Model id", default_model) or default_model
    return shown[choice - 1]


def _prioritise(candidates: List[str], default_model: str) -> List[str]:
    ordered = [model for model in candidates if model == default_model]
    ordered += [model for model in candidates if model != default_model]
    return ordered


def _save(
    providers: Dict[str, Dict[str, str]],
    writer: Tuple[str, str],
    judge: Tuple[str, str],
    say: Say,
    target: Path,
) -> Path:
    roles: Dict[str, Tuple[str, str]] = {role: writer for role in MAIN_ROLES}
    roles["judge"] = judge
    config = UserConfig.from_choices(providers=providers, roles=roles)
    saved = write_user_config(config, target)
    say("")
    say(config.summary())
    say("")
    say(f"Saved to {saved}.")
    say("Next: `book-genesis new` to write a book, or `book-genesis doctor` to check this again.")
    return saved


def _menu(ask: Ask, say: Say, question: str, options: List[str], default: int = 1) -> int:
    for number, option in enumerate(options, 1):
        say(f"  {number}) {option}")
    answer = (ask(f"{question} [1-{len(options)}]", str(default)) or str(default)).strip()
    try:
        chosen = int(answer)
    except ValueError:
        return default
    return chosen if 1 <= chosen <= len(options) else default


def _plan_line(plan: Optional[QuickPlan]) -> str:
    if plan is None:
        return "nothing detected"
    if plan.single_family:
        return f"{plan.writer.label} writes and judges"
    return f"{plan.writer.label} writes, {plan.judge.label} judges"


def _default_verifier(adapter_name: str, model: str, provider: Optional[Dict[str, str]]) -> Tuple[bool, str]:
    from runner.roles import build_adapter

    if adapter_name == "manual":
        return True, "manual mode, nothing to check"
    user_config = None
    if provider is not None:
        user_config = UserConfig.from_choices(providers={adapter_name: provider}, roles={})
    try:
        adapter = build_adapter(adapter_name, user_config=user_config)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return verify_candidate(adapter, model)


__all__ = ["run_setup", "MENU", "BY_KEY", "Preset"]
