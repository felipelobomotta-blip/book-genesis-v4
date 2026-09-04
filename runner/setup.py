"""`book-genesis setup`: the onboarding wizard (ADR 0003, revised by ADR 0004, 0005, 0007).

Shaped like the onboarding of OpenClaw, Hermes and opencode: a banner, a plain-language
explanation of what writer/judge mean, detection of what the machine can already run, a
one-keystroke quick start, a real completion to prove the choice before anything is saved.
Re-running is a verification pass: "Change it" keeps the providers and keys already stored.

Models are never a static list typed into this file. API providers are listed live from the
provider (`/models`), filtered to chat models and sorted newest first. Subscription CLIs
(Claude Code, Codex) are probed: one tiny real call per candidate id, in parallel, cached for
a week in ~/.book-genesis/models-cache.json. The candidate ids come from the providers' own
documentation and are only ever inputs to the probe, never asserted.

Menu selection goes through an injectable ``choose`` callable (arrow keys on a real
terminal, typed number otherwise; tests always use the typed one).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable, Dict, List, Optional, Tuple

from runner.constants import DEFAULT_PERSONAS, PanelSpec
from runner.onboarding import (
    Detection,
    QuickPlan,
    cached_models,
    chat_models_only,
    detect_environment,
    list_models,
    probe_models,
    quick_plan,
    sort_models,
    store_models,
    verify_candidate,
)
from runner.tui import banner
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


# The provider menu, in the order it is shown. The numbers/positions are part of the interface.
# Defaults follow the providers' own docs (Anthropic: "start with Claude Opus 5"; Sonnet 5 is
# "the best combination of speed and intelligence") and what this machine's CLIs actually
# accepted when probed (Codex: gpt-5.5, its own default).
MENU: List[Preset] = [
    Preset("claude", "Claude subscription (OAuth through the Claude Code CLI, no key)", "cli", "", "", "claude-opus-5", "claude-sonnet-5", needs_key=False),
    Preset("codex", "ChatGPT / Codex subscription (OAuth through the Codex CLI, no key)", "cli", "", "", "gpt-5.5", "gpt-5.5", needs_key=False),
    Preset("openrouter", "OpenRouter", "openai", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "anthropic/claude-opus-5", "deepseek/deepseek-v4-pro"),
    Preset("deepseek", "DeepSeek", "openai", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", "deepseek-chat", "deepseek-chat"),
    Preset("anthropic", "Anthropic", "anthropic", "https://api.anthropic.com", "ANTHROPIC_API_KEY", "claude-opus-5", "claude-sonnet-5"),
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

# Candidate ids for the subscription CLIs, from the providers' documentation and public
# catalogs (platform.claude.com models overview; OpenRouter catalog for OpenAI ids). They are
# inputs to a real probe, never shown unverified. Aliases last: they resolve to "the newest".
CLI_CANDIDATES: Dict[str, List[str]] = {
    "claude": [
        "claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5-20251001", "claude-fable-5-1",
        "claude-opus-4-8", "claude-opus-4-7", "claude-opus-4-6", "claude-opus-4-5", "claude-opus-4-1",
        "claude-sonnet-4-6", "claude-sonnet-4-5",
        "opus", "sonnet", "haiku",
    ],
    "codex": [
        "gpt-5.5", "gpt-5.5-pro", "gpt-5.4", "gpt-5.4-mini", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
        "gpt-5.2", "gpt-5.1", "o3", "o4-mini", "gpt-4.1",
    ],
}
# If the probe finds nothing (offline, cache unreadable), the wizard must not dead-end.
CLI_FALLBACK: Dict[str, List[str]] = {"claude": ["opus", "sonnet", "haiku"], "codex": ["gpt-5.5"]}
ALIASES = {"opus": "alias: always the newest Opus", "sonnet": "alias: always the newest Sonnet", "haiku": "alias: always the newest Haiku"}
OAUTH_HELP = {
    "claude": "Install Claude Code (`npm install -g @anthropic-ai/claude-code`), run `claude` once and log in; that login is the OAuth.",
    "codex": "Install the Codex CLI (`npm install -g @openai/codex`), run `codex login`; that login is the OAuth.",
}
MAX_MODELS_SHOWN = 15
CHEAPER_CLAUDE = {"disruptor": "claude-sonnet-5", "extractor": "claude-haiku-4-5-20251001"}

# One line per role, said before the model list: the person should not need to know what a
# judge needs. The recommended model is pre-selected; Enter is a correct answer.
ROLE_GUIDANCE = {
    "writing": "The writer is where the prose comes from: the one role worth the strongest model you can afford.",
    "judging": (
        "The judge only reads and answers, but it runs on every chapter and every revision. "
        "A balanced model is usually right; a different provider from the writer matters more than the most expensive one."
    ),
}
_PREMIUM_HINTS = ("opus", "fable", "pro", "ultra", "sol", "astra", "o3", "o1", "large", "reasoner", "r1")
_BUDGET_HINTS = ("mini", "nano", "haiku", "flash", "lite", "small", "luna")


def tag_model(model_id: str) -> str:
    """A plain-language tier for a model id, from the naming every provider shares:
    mini/nano/haiku/flash/lite/luna mean cheaper and faster; opus/fable/pro/ultra/sol/o-series
    mean the flagship. A hint about tier, not a price list. Budget wins when both appear
    (o3-mini). Whole tokens only: "gemini" contains "mini" and is not a budget model."""
    tokens = {token for token in re.split(r"[^a-z0-9]+", model_id.lower()) if token}
    if tokens & set(_BUDGET_HINTS):
        return "cheaper, fine for mechanical roles"
    if tokens & set(_PREMIUM_HINTS):
        return "pricier, the strongest for writing a book"
    return "best cost/quality balance"


Ask = Callable[..., str]
Secret = Callable[[str], str]
Say = Callable[..., None]
Choose = Callable[[str, List[str], int], int]
Verifier = Callable[[str, str, Optional[Dict[str, str]]], Tuple[bool, str]]
Lister = Callable[[str, str, str], List[str]]
Prober = Callable[[str], List[str]]


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
    choose: Optional[Choose] = None,
    prober: Optional[Prober] = None,
    cache_path: Optional[Path] = None,
) -> Optional[Path]:
    """Returns the config path, or None when the person skipped or a check failed."""
    target = user_config_path(path)
    check = verifier or _default_verifier
    models_of = lister or list_models
    picker = choose or text_choose(ask, say)
    cli_models_of = prober or _default_prober(say, cache_path)
    found = detect_environment(available=available) if detections is None else list(detections)

    say("")
    say(banner())
    say("")
    say("This decides who writes your book and who judges each chapter.")
    say("  - The WRITER drafts every chapter from the outline.")
    say("  - The JUDGE reads each chapter blind - no outline, no plan - and says whether")
    say("    it would turn the page. A model grading its own prose trusts itself too much,")
    say("    so a different provider for the judge is the stronger setup.")
    say("Nothing typed here leaves this machine. Keys are stored locally or read from your environment.")
    say("")

    providers: Dict[str, Dict[str, str]] = {}
    if target.exists():
        existing = load_user_config(target)
        say(f"You already have a configuration at {target}:")
        if existing is not None:
            say(existing.summary())
        say("")
        choice = picker("What do you want to do", ["Keep it as it is", "Change it (keeps the providers and keys already stored)", "Reset and start over (drops stored keys)"], 1)
        if choice == 1:
            say("Kept. Run `book-genesis doctor` to check it, or `book-genesis new` to write a book.")
            return target
        if choice == 3:
            say("Starting over. Stored provider keys are dropped.")
        elif existing is not None:
            providers = _provider_entries(existing)
            if providers:
                say(f"Keeping stored providers: {', '.join(providers)}.")

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
    choice = picker("How do you want to run the models", options, 1 if plan else 2)
    if choice == 3:
        say("Skipped. Run `book-genesis setup` whenever you want.")
        return None
    if choice == 1 and plan is not None:
        return _quick(plan, ask, secret, say, target, check, providers)
    return _custom(ask, secret, say, target, check, found, models_of, picker, cli_models_of, providers)


def _provider_entries(config: UserConfig) -> Dict[str, Dict[str, str]]:
    entries: Dict[str, Dict[str, str]] = {}
    for provider in config.providers.values():
        entry: Dict[str, str] = {"type": provider.type, "base_url": provider.base_url}
        if provider.api_key:
            entry["api_key"] = provider.api_key
        elif provider.api_key_env:
            entry["api_key_env"] = provider.api_key_env
        entries[provider.name] = entry
    return entries


def _quick(
    plan: QuickPlan,
    ask: Ask,
    secret: Secret,
    say: Say,
    target: Path,
    check: Verifier,
    providers: Dict[str, Dict[str, str]],
) -> Optional[Path]:
    say("")
    writer = _entry_for(plan.writer.key, "writing", providers, ask, secret, say, None, None, interactive=False)
    judge = writer if plan.single_family else _entry_for(plan.judge.key, "judging", providers, ask, secret, say, None, None, interactive=False)
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
    picker: Choose,
    cli_models_of: Prober,
    providers: Dict[str, Dict[str, str]],
) -> Optional[Path]:
    detected = {detection.key for detection in found}
    labels = [preset.label + (" [detected]" if preset.key in detected else "") for preset in MENU]

    say("")
    index = picker("Provider for writing (writer, editor, architect)", labels, 1)
    key = MENU[index - 1].key
    if key in OAUTH_HELP and key not in detected:
        say(f"  {OAUTH_HELP[key]}")
    writer = _entry_for(key, "writing", providers, ask, secret, say, models_of, cli_models_of, interactive=True, picker=picker)

    say("")
    judge_labels = labels + ["Same as writing"]
    judge_index = picker("Provider for judging (a different one is a stronger gate)", judge_labels, len(judge_labels))
    if judge_index == len(judge_labels):
        default_model = BY_KEY[writer[0]].judge_model if writer[0] in BY_KEY else writer[1]
        judge = (writer[0], _pick_model(writer[0], "judging", default_model, providers, ask, say, models_of, cli_models_of, picker) or writer[1])
    else:
        key = MENU[judge_index - 1].key
        if key in OAUTH_HELP and key not in detected:
            say(f"  {OAUTH_HELP[key]}")
        judge = _entry_for(key, "judging", providers, ask, secret, say, models_of, cli_models_of, interactive=True, picker=picker)

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
    cli_models_of: Optional[Prober],
    *,
    interactive: bool,
    picker: Optional[Choose] = None,
) -> Tuple[str, str]:
    preset = BY_KEY[key]
    default_model = preset.writer_model if purpose == "writing" else preset.judge_model
    if preset.type in ("cli", "manual"):
        if not interactive:
            return key, default_model
        return key, _pick_model(key, purpose, default_model, providers, ask, say, models_of, cli_models_of, picker)
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
    return key, _pick_model(key, purpose, default_model, providers, ask, say, models_of, cli_models_of, picker) or default_model


def _pick_model(
    key: str,
    purpose: str,
    default_model: str,
    providers: Dict[str, Dict[str, str]],
    ask: Ask,
    say: Say,
    models_of: Optional[Lister],
    cli_models_of: Optional[Prober],
    picker: Optional[Choose] = None,
) -> str:
    """A list of real model ids: live from the provider for API keys, probed for the CLIs.
    Newest first, every entry tagged by tier, the recommended one marked and pre-selected."""
    guidance = ROLE_GUIDANCE.get(purpose)
    if guidance:
        say(f"  {guidance}")
    candidates: List[str] = []
    if key in CLI_CANDIDATES:
        if cli_models_of is not None:
            candidates = list(cli_models_of(key))
        if not candidates:
            candidates = list(CLI_FALLBACK.get(key, []))
    elif models_of is not None and key in providers:
        entry = providers[key]
        api_key = entry.get("api_key", "")
        if not api_key and entry.get("api_key_env"):
            import os

            api_key = os.environ.get(entry["api_key_env"], "")
        candidates = chat_models_only(models_of(entry.get("type", "openai"), entry.get("base_url", ""), api_key))
    if not candidates:
        return ask(f"Model for {purpose} on {key}", default_model) or default_model
    shown = _prioritise(sort_models(candidates), default_model)[:MAX_MODELS_SHOWN]
    display = [_display(model, model == default_model) for model in shown]
    options = display + ["Type another model id"]
    default_index = shown.index(default_model) + 1 if default_model in shown else 1
    chooser = picker or text_choose(ask, say)
    choice = chooser(f"Model for {purpose} on {key}", options, default_index)
    if choice == len(options):
        return ask("Model id", default_model) or default_model
    return shown[choice - 1]


def _display(model: str, recommended: bool) -> str:
    note = ALIASES.get(model, tag_model(model))
    if recommended:
        note += ", recommended"
    return f"{model}  ({note})"


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
    writer_adapter, writer_model = writer
    roles: Dict[str, Tuple[str, str]] = {}
    for role in MAIN_ROLES:
        model = writer_model
        if writer_adapter == "claude" and role in CHEAPER_CLAUDE:
            model = CHEAPER_CLAUDE[role]
        roles[role] = (writer_adapter, model)
    roles["judge"] = judge
    config = UserConfig.from_choices(providers=providers, roles=roles, panel=_panel_seats(writer, judge))
    saved = write_user_config(config, target)
    say("")
    say(config.summary())
    say("")
    say(f"Saved to {saved}.")
    say("Next: `book-genesis new` to write a book, or `book-genesis doctor` to check this again.")
    return saved


def _panel_seats(writer: Tuple[str, str], judge: Tuple[str, str]) -> List[PanelSpec]:
    """Three blind seats. With two providers the middle seat comes from the writer's family,
    so the panel never speaks with one voice; with one provider, all three sit on the judge."""
    judge_adapter, judge_model = judge
    writer_adapter, writer_model = writer
    if writer_adapter == judge_adapter:
        seats = [(judge_adapter, judge_model)] * 3
    else:
        middle_model = BY_KEY[writer_adapter].judge_model if writer_adapter in BY_KEY and BY_KEY[writer_adapter].judge_model else writer_model
        seats = [(judge_adapter, judge_model), (writer_adapter, middle_model), (judge_adapter, judge_model)]
    return [PanelSpec(adapter, model, persona) for (adapter, model), persona in zip(seats, DEFAULT_PERSONAS)]


def text_choose(ask: Ask, say: Say) -> Choose:
    """The plain-text fallback: print '  N) label' for each option, then ask for a number.
    Used whenever there is no real terminal to draw an arrow-key menu on - including every
    automated test."""

    def choose(question: str, options: List[str], default: int) -> int:
        for number, option in enumerate(options, 1):
            say(f"  {number}) {option}")
        answer = (ask(f"{question} [1-{len(options)}]", str(default)) or str(default)).strip()
        try:
            chosen = int(answer)
        except ValueError:
            return default
        return chosen if 1 <= chosen <= len(options) else default

    return choose


def _plan_line(plan: Optional[QuickPlan]) -> str:
    if plan is None:
        return "nothing detected"
    if plan.single_family:
        return f"{plan.writer.label} writes and judges"
    return f"{plan.writer.label} writes, {plan.judge.label} judges"


def _default_prober(say: Say, cache_path: Optional[Path]) -> Prober:
    """Real probing of a subscription CLI, cached for a week. Deleting
    ~/.book-genesis/models-cache.json forces a fresh probe."""

    def probe(key: str) -> List[str]:
        from runner.roles import build_adapter

        cached = cached_models(key, cache_path)
        if cached is not None:
            say(f"  Models your {key} accepts (checked earlier this week; delete models-cache.json to re-check).")
            return cached
        try:
            adapter = build_adapter(key)
        except Exception as exc:  # noqa: BLE001
            say(f"  could not build the {key} adapter: {exc}")
            return []
        candidates = CLI_CANDIDATES.get(key, [])
        say(f"  Checking which of {len(candidates)} model ids your {key} accepts: one tiny call each, in parallel, about a minute...")

        def report(candidate: str, ok: bool) -> None:
            say(f"    {'ok  ' if ok else 'no  '} {candidate}")

        accepted = probe_models(adapter, candidates, on_result=report)
        store_models(key, accepted, cache_path)
        return accepted

    return probe


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


__all__ = ["run_setup", "MENU", "BY_KEY", "Preset", "text_choose", "Choose", "tag_model", "ROLE_GUIDANCE", "CLI_CANDIDATES"]
