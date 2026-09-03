"""`book-genesis setup`: the person chooses how models run, once (ADR 0003).

Questions come through injectable ``ask`` / ``secret`` / ``say`` callables so the flow is
testable with scripted answers. Keys are read with the hidden ``secret`` prompt and written
only to the user config; a blank key means "use the environment variable".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from runner.constants import ROLES
from runner.roles import available_adapters
from runner.userconfig import UserConfig, write_user_config


@dataclass(frozen=True)
class Preset:
    type: str
    base_url: str
    key_env: str
    writer_model: str
    judge_model: str
    needs_key: bool = True


PRESETS: Dict[str, Preset] = {
    "openrouter": Preset("openai", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "anthropic/claude-sonnet-4.5", "deepseek/deepseek-chat"),
    "deepseek": Preset("openai", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY", "deepseek-chat", "deepseek-chat"),
    "anthropic": Preset("anthropic", "https://api.anthropic.com", "ANTHROPIC_API_KEY", "claude-sonnet-5", "claude-sonnet-5"),
    "openai": Preset("openai", "https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-5.5", "gpt-5.5"),
    "groq": Preset("openai", "https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile", "llama-3.3-70b-versatile"),
    "together": Preset("openai", "https://api.together.xyz/v1", "TOGETHER_API_KEY", "meta-llama/Llama-3.3-70B-Instruct-Turbo", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    "ollama": Preset("openai", "http://localhost:11434/v1", "", "llama3.1", "llama3.1", needs_key=False),
    "lmstudio": Preset("openai", "http://localhost:1234/v1", "", "", "", needs_key=False),
}
CLI_CHOICES = ("claude", "codex")
CLI_MODELS = {"claude": {"writing": "opus", "judging": "sonnet"}, "codex": {"writing": "", "judging": ""}}
MAIN_ROLES = ("writer", "editor", "architect", "disruptor", "extractor")

Ask = Callable[[str, str], str]
Secret = Callable[[str], str]
Say = Callable[[str], None]


def run_setup(
    *,
    ask: Ask,
    secret: Secret,
    say: Say,
    path: Optional[Path] = None,
    available: Optional[Dict[str, bool]] = None,
) -> Path:
    found = available if available is not None else available_adapters()
    installed = [name for name in CLI_CHOICES if found.get(name)]
    options = installed + [name for name in PRESETS] + ["other", "manual"]

    say("Book Genesis setup. Nothing typed here leaves this machine. Keys go to the user config only.")
    if installed:
        say("Installed CLIs found: " + ", ".join(installed) + " (they use the session already logged in; no key needed).")

    providers: Dict[str, Dict[str, str]] = {}
    main = _choose(ask, "Main provider (writer, editor, architect)", options, default=installed[0] if installed else "openrouter")
    main_adapter, main_model = _configure(main, "writing", ask, secret, providers)

    recommended = next((name for name in installed if name != main), "same")
    judge_options = options + ["same"]
    judge = _choose(
        ask,
        "Judge and reader panel (a different family is a stronger gate; 'same' reuses the main provider)",
        judge_options,
        default=recommended,
    )
    if judge == "same" or judge == main:
        judge_adapter = main_adapter
        judge_model = ask(f"Model for judging on {main}", _judge_default(main, main_model)) or main_model
    else:
        judge_adapter, judge_model = _configure(judge, "judging", ask, secret, providers)

    roles: Dict[str, Tuple[str, str]] = {role: (main_adapter, main_model) for role in MAIN_ROLES}
    roles["judge"] = (judge_adapter, judge_model)
    config = UserConfig.from_choices(providers=providers, roles=roles)
    target = write_user_config(config, path)
    say(config.summary())
    say(f"Saved to {target}. Run `book-genesis doctor` to check it, then `book-genesis new`.")
    return target


def _choose(ask: Ask, question: str, options: List[str], default: str) -> str:
    answer = (ask(f"{question} [{', '.join(options)}]", default) or default).strip().lower()
    return answer if answer in options else default


def _configure(name: str, purpose: str, ask: Ask, secret: Secret, providers: Dict[str, Dict[str, str]]) -> Tuple[str, str]:
    if name in CLI_CHOICES:
        model = ask(f"Model for {purpose} on {name}", CLI_MODELS[name][purpose])
        return name, model
    if name == "manual":
        return "manual", ""
    if name == "other":
        if "other" not in providers:
            base_url = ask("Base URL of the OpenAI-compatible endpoint (ends in /v1)", "")
            env = ask("Environment variable holding the key", "OTHER_API_KEY")
            key = secret("API key (blank = use the environment variable)")
            providers["other"] = {"type": "openai", "base_url": base_url}
            providers["other"]["api_key" if key else "api_key_env"] = key or env
        model = ask(f"Model for {purpose}", "")
        return "other", model

    preset = PRESETS[name]
    if name not in providers:
        base_url = ask(f"Base URL for {name}", preset.base_url) or preset.base_url
        entry: Dict[str, str] = {"type": preset.type, "base_url": base_url}
        if preset.needs_key:
            key = secret(f"API key for {name} (blank = use env {preset.key_env})")
            if key:
                entry["api_key"] = key
            else:
                entry["api_key_env"] = preset.key_env
        else:
            entry["api_key"] = "none"
        providers[name] = entry
    default_model = preset.writer_model if purpose == "writing" else preset.judge_model
    model = ask(f"Model for {purpose} on {name}", default_model) or default_model
    return name, model


def _judge_default(name: str, main_model: str) -> str:
    if name in CLI_CHOICES:
        return CLI_MODELS[name]["judging"]
    if name in PRESETS:
        return PRESETS[name].judge_model or main_model
    return main_model


__all__ = ["run_setup", "PRESETS", "CLI_CHOICES", "ROLES"]
