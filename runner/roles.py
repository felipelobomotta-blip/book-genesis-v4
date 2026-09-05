"""Discover what is installed and assign every role and every panel seat (ADR 0002).

The configured map in runner/config/models.yaml is a preference, not a requirement: a
role whose adapter is not on this machine falls back to what is. The judge prefers a
different family than the writer; when only one family exists the judge takes a
different model and the plan carries a "single family" warning that ends up in
RUN_REPORT.md. Nothing here reads an API key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
from typing import Dict, List, Optional

from runner.adapters import (
    Adapter,
    AdapterError,
    AnthropicAdapter,
    ClaudeCliAdapter,
    CodexCliAdapter,
    FakeAdapter,
    GenericCliAdapter,
    ManualAdapter,
    OpenAICompatibleAdapter,
    command_template_argv,
)
from runner.constants import (
    DEFAULT_PERSONAS,
    ROLES,
    PanelSpec,
    load_generic_adapter_requirements,
    RoleModel,
    load_generic_adapters,
    load_model_map,
    load_panel,
)
from runner.panel import PanelJudge, PanelMember

FAKE_SEPARATOR = "=== NEXT ==="
KNOWN_CLIS = ("claude", "codex")

_CLAUDE_DEFAULTS = {
    "writer": "opus",
    "editor": "opus",
    "architect": "opus",
    "judge": "sonnet",
    "disruptor": "sonnet",
    "extractor": "haiku",
}
_CLAUDE_ALTERNATIVE = {"opus": "sonnet", "sonnet": "opus", "haiku": "sonnet"}


@dataclass
class RolePlan:
    roles: Dict[str, RoleModel]
    panel: List[PanelSpec]
    warnings: List[str] = field(default_factory=list)


@dataclass
class RunSetup:
    adapters: Dict[str, Adapter]
    models: Dict[str, str]
    panel: Optional[PanelJudge]
    warnings: List[str] = field(default_factory=list)


def available_adapters() -> Dict[str, bool]:
    found = {name: shutil.which(name) is not None for name in KNOWN_CLIS}
    requirements = load_generic_adapter_requirements()
    for name, template in load_generic_adapters().items():
        try:
            argv = command_template_argv(template)
        except AdapterError:
            found[name] = False
            continue
        head = argv[0] if argv else ""
        needed = requirements.get(name) or ([head] if head else [])
        found[name] = bool(needed) and all(
            shutil.which(executable) is not None or Path(executable).is_file()
            for executable in needed
        )
    return found


def plan_roles(available: Optional[Dict[str, bool]] = None, user_config=None) -> RolePlan:
    found = dict(available) if available is not None else available_adapters()
    if user_config is not None:
        for name in user_config.providers:
            found[name] = True
    installed = [name for name in KNOWN_CLIS if found.get(name)]
    installed += [name for name, ok in found.items() if ok and name not in KNOWN_CLIS]
    if not installed:
        raise AdapterError(
            "no model provider available. Run `book-genesis setup` to connect an API key (OpenRouter, DeepSeek, "
            "Anthropic, OpenAI, a local server), install Claude Code (`claude`) or the Codex CLI (`codex`), "
            "declare another CLI in runner/config/adapters.yaml, or run with `--manual`."
        )
    fallback = installed[0]

    configured = load_model_map()
    if user_config is not None:
        configured.update(user_config.roles)
    roles: Dict[str, RoleModel] = {}
    for role in ROLES:
        wanted = configured.get(role, RoleModel(fallback, ""))
        if found.get(wanted.adapter):
            roles[role] = wanted
        else:
            roles[role] = RoleModel(fallback, _default_model(fallback, role, user_config))

    warnings: List[str] = []
    writer, judge = roles["writer"], roles["judge"]
    if writer.adapter == judge.adapter:
        # Respect explicit user choice (e.g. "muse spark pra fazer tudo") — ADR 0002
        # bias avoidance is a default, not an override.
        explicitly_same = (
            user_config is not None
            and "judge" in user_config.roles
            and user_config.roles["judge"].adapter == writer.adapter
        )
        if explicitly_same:
            if not judge.model or judge.model == writer.model:
                # Keep exactly what the user asked for; still surface a warning
                pass
            warnings.append(
                f"single family: writer and judge both run on `{writer.adapter}` "
                f"as explicitly configured. A judge from another family is a stronger gate."
            )
        else:
            other = [name for name in installed if name != writer.adapter]
            if other:
                roles["judge"] = RoleModel(other[0], _default_model(other[0], "judge"))
            else:
                if not judge.model or judge.model == writer.model:
                    roles["judge"] = RoleModel(writer.adapter, _different_model(writer.adapter, writer.model))
                warnings.append(
                    f"single family: writer and judge both run on `{writer.adapter}` "
                    f"(judge model {roles['judge'].model or 'default'}). A judge from another family is a stronger "
                    "gate; install a second CLI when you can."
                )

    panel: List[PanelSpec] = []
    user_panel = user_config is not None and bool(user_config.panel)
    seats = user_config.panel if user_panel else load_panel()
    for spec in seats:
        if found.get(spec.adapter):
            panel.append(spec)
        else:
            model = spec.model if (fallback == "claude" and spec.model) else _default_model(fallback, "judge", user_config)
            panel.append(PanelSpec(fallback, model, spec.persona))
    if not panel:
        panel = [PanelSpec(fallback, _default_model(fallback, "judge", user_config), persona) for persona in DEFAULT_PERSONAS]
    panel = _distinct_personas(panel)
    if (
        not user_panel
        and len({spec.adapter for spec in panel}) == 1
        and not any(w.startswith("single family") for w in warnings)
    ):
        warnings.append(f"single family: the reader panel runs entirely on `{panel[0].adapter}`.")

    return RolePlan(roles=roles, panel=panel, warnings=warnings)


def load_fake_responses(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    parts = [part.strip("\r\n") for part in text.split(FAKE_SEPARATOR)]
    return [part for part in parts if part.strip()]


def build_adapter(
    name: str,
    *,
    fake_responses: Optional[List[str]] = None,
    manual_dir: Optional[Path] = None,
    role: str = "",
    user_config=None,
) -> Adapter:
    normalized = name.strip().lower()
    if normalized == "fake":
        return FakeAdapter(fake_responses or [])
    if normalized == "claude":
        return ClaudeCliAdapter()
    if normalized == "codex":
        return CodexCliAdapter()
    if normalized == "manual":
        if manual_dir is None:
            raise AdapterError("the manual adapter needs a project: run `chapter`, `book`, `run-phase` or `panel` with --manual")
        return ManualAdapter(manual_dir, role or "model")
    if user_config is not None and normalized in user_config.providers:
        provider = user_config.providers[normalized]
        try:
            key = provider.resolve_key()
        except AdapterError:
            key = ""  # reported by `doctor`; the call itself fails with a clear message
        if provider.type == "anthropic":
            return AnthropicAdapter(provider.name, provider.base_url, key)
        return OpenAICompatibleAdapter(provider.name, provider.base_url, key)
    generic = load_generic_adapters()
    if normalized in generic:
        return GenericCliAdapter(normalized, generic[normalized])
    raise AdapterError(
        f"unknown adapter {name!r}; use claude, codex, manual, fake, a provider from `book-genesis setup`, "
        "or a name declared in runner/config/adapters.yaml"
    )


def build_role_adapters(
    *,
    fake_responses_path: Optional[Path] = None,
    available: Optional[Dict[str, bool]] = None,
    manual_dir: Optional[Path] = None,
    user_config=None,
) -> RunSetup:
    """Adapters and models per role plus the reader panel.

    With ``fake_responses_path`` every role and every panel seat shares one scripted adapter,
    so responses are consumed in call order (writer, disruptor, judge or panel seats, editor...).
    With ``manual_dir`` every call becomes a prompt file a person answers by hand.
    """
    if fake_responses_path is not None:
        shared = FakeAdapter(load_fake_responses(fake_responses_path))
        panel = PanelJudge([PanelMember(shared, "", persona) for persona in DEFAULT_PERSONAS])
        return RunSetup({role: shared for role in ROLES}, {role: "" for role in ROLES}, panel, [])

    if manual_dir is not None:
        adapters: Dict[str, Adapter] = {role: ManualAdapter(manual_dir, role) for role in ROLES}
        panel = PanelJudge(
            [
                PanelMember(ManualAdapter(manual_dir, f"panel{index}"), "", persona)
                for index, persona in enumerate(DEFAULT_PERSONAS, 1)
            ]
        )
        note = (
            f"manual: every model call becomes a prompt file under {manual_dir}; paste each reply into the "
            "matching .response.md and run the same command again"
        )
        return RunSetup(adapters, {role: "" for role in ROLES}, panel, [note])

    plan = plan_roles(available, user_config)
    cache: Dict[str, Adapter] = {}

    def get(name: str) -> Adapter:
        if name not in cache:
            cache[name] = build_adapter(name, user_config=user_config)
        return cache[name]

    adapters = {role: get(role_model.adapter) for role, role_model in plan.roles.items()}
    models = {role: role_model.model for role, role_model in plan.roles.items()}
    panel = PanelJudge([PanelMember(get(spec.adapter), spec.model, spec.persona) for spec in plan.panel])
    return RunSetup(adapters, models, panel, list(plan.warnings))


def _default_model(adapter: str, role: str, user_config=None) -> str:
    if adapter == "claude":
        return _CLAUDE_DEFAULTS.get(role, "sonnet")
    if user_config is not None and adapter in user_config.providers:
        for configured_role in ("writer", "judge", "editor", "architect", "disruptor", "extractor"):
            role_model = user_config.roles.get(configured_role)
            if role_model is not None and role_model.adapter == adapter and role_model.model:
                return role_model.model
    return ""


def _different_model(adapter: str, model: str) -> str:
    if adapter == "claude":
        return _CLAUDE_ALTERNATIVE.get(model, "sonnet")
    return ""


def _distinct_personas(panel: List[PanelSpec]) -> List[PanelSpec]:
    seen: Dict[str, int] = {}
    result: List[PanelSpec] = []
    for index, spec in enumerate(panel):
        persona = spec.persona or DEFAULT_PERSONAS[index % len(DEFAULT_PERSONAS)]
        if persona in seen:
            seen[persona] += 1
            persona = f"{persona} ({seen[persona]})"
        else:
            seen[persona] = 1
        result.append(PanelSpec(spec.adapter, spec.model, persona))
    return result
