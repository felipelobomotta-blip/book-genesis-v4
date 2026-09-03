"""The person's own choices: providers, keys, roles (ADR 0003).

Lives in ``~/.book-genesis/config.yaml`` (override with the BOOK_GENESIS_CONFIG environment
variable). When it exists it wins over runner/config/models.yaml. Keys come from an
environment variable (``api_key_env``) or from the file itself (``api_key``); they are never
printed and never written anywhere else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from runner.adapters import AdapterError
from runner.constants import DEFAULT_PERSONAS, ROLES, PanelSpec, RoleModel
from runner.filesystem import load_simple_yaml_map

CONFIG_ENV = "BOOK_GENESIS_CONFIG"
DEFAULT_USER_CONFIG_PATH = Path.home() / ".book-genesis" / "config.yaml"
PROVIDER_PREFIX = "provider_"


@dataclass(frozen=True)
class Provider:
    name: str
    type: str
    base_url: str
    api_key: str = ""
    api_key_env: str = ""

    def resolve_key(self) -> str:
        if self.api_key:
            return self.api_key
        if self.api_key_env:
            value = os.environ.get(self.api_key_env, "")
            if value:
                return value
            raise AdapterError(
                f"provider {self.name}: environment variable {self.api_key_env} is not set. "
                "Set it, or run `book-genesis setup` to store the key locally."
            )
        raise AdapterError(f"provider {self.name}: no API key configured. Run `book-genesis setup`.")

    def key_status(self) -> str:
        try:
            self.resolve_key()
        except AdapterError:
            return f"missing (env {self.api_key_env})" if self.api_key_env else "missing"
        if self.api_key:
            return "set (in config file)"
        return f"set (env {self.api_key_env})"


@dataclass
class UserConfig:
    providers: Dict[str, Provider] = field(default_factory=dict)
    roles: Dict[str, RoleModel] = field(default_factory=dict)
    panel: List[PanelSpec] = field(default_factory=list)
    path: Optional[Path] = None

    @classmethod
    def from_choices(
        cls,
        *,
        providers: Dict[str, Dict[str, str]],
        roles: Dict[str, Tuple[str, str]],
        panel: Optional[List[PanelSpec]] = None,
    ) -> "UserConfig":
        provider_objects = {
            name: Provider(
                name=name,
                type=values.get("type", "openai"),
                base_url=values.get("base_url", ""),
                api_key=values.get("api_key", ""),
                api_key_env=values.get("api_key_env", ""),
            )
            for name, values in providers.items()
        }
        role_models = {role: RoleModel(adapter, model) for role, (adapter, model) in roles.items()}
        if panel is None:
            seat = role_models.get("judge") or role_models.get("writer")
            panel = [PanelSpec(seat.adapter, seat.model, persona) for persona in DEFAULT_PERSONAS] if seat else []
        return cls(provider_objects, role_models, list(panel))

    def summary(self) -> str:
        lines = [f"user config: {self.path or DEFAULT_USER_CONFIG_PATH}"]
        if self.providers:
            lines.append("providers:")
            for provider in self.providers.values():
                lines.append(f"  {provider.name}: {provider.type} at {provider.base_url}; key {provider.key_status()}")
        if self.roles:
            lines.append("roles:")
            for role in ROLES:
                if role in self.roles:
                    model = self.roles[role]
                    lines.append(f"  {role}: {model.adapter}{' ' + model.model if model.model else ''}")
        if self.panel:
            lines.append("panel:")
            for seat in self.panel:
                lines.append(f"  {seat.adapter}{' ' + seat.model if seat.model else ''} as {seat.persona}")
        return "\n".join(lines)


def user_config_path(path: Optional[Path] = None) -> Path:
    if path is not None:
        return Path(path)
    override = os.environ.get(CONFIG_ENV, "")
    return Path(override) if override else DEFAULT_USER_CONFIG_PATH


def load_user_config(path: Optional[Path] = None) -> Optional[UserConfig]:
    target = user_config_path(path)
    if not target.exists():
        return None
    entries = load_simple_yaml_map(target)
    providers: Dict[str, Provider] = {}
    roles: Dict[str, RoleModel] = {}
    panel: List[PanelSpec] = []
    for key, values in entries.items():
        if key.startswith(PROVIDER_PREFIX):
            name = key[len(PROVIDER_PREFIX) :].strip().lower()
            providers[name] = Provider(
                name=name,
                type=str(values.get("type", "openai")).strip().lower(),
                base_url=str(values.get("base_url", "")).strip(),
                api_key=str(values.get("api_key", "")).strip(),
                api_key_env=str(values.get("api_key_env", "")).strip(),
            )
        elif key in ROLES:
            roles[key] = RoleModel(str(values.get("adapter", "")).strip(), str(values.get("model", "")).strip())
        elif key.startswith("panel"):
            panel.append(
                PanelSpec(
                    str(values.get("adapter", "")).strip(),
                    str(values.get("model", "")).strip(),
                    str(values.get("persona", "")).strip(),
                )
            )
    return UserConfig(providers=providers, roles=roles, panel=panel, path=target)


def write_user_config(config: UserConfig, path: Optional[Path] = None) -> Path:
    target = user_config_path(path)
    lines = [
        "# Book Genesis user configuration, written by `book-genesis setup`.",
        "# This file wins over runner/config/models.yaml. Keys stored here never leave this machine;",
        "# prefer api_key_env when you can. Never commit this file.",
        "",
    ]
    for provider in config.providers.values():
        lines += [f"{PROVIDER_PREFIX}{provider.name}:", f"  type: {provider.type}", f"  base_url: {provider.base_url}"]
        if provider.api_key:
            lines.append(f"  api_key: {provider.api_key}")
        elif provider.api_key_env:
            lines.append(f"  api_key_env: {provider.api_key_env}")
        lines.append("")
    for role in ROLES:
        if role in config.roles:
            model = config.roles[role]
            lines += [f"{role}:", f"  adapter: {model.adapter}", f"  model: {_yaml_scalar(model.model)}", ""]
    for index, seat in enumerate(config.panel, 1):
        lines += [
            f"panel_{index}:",
            f"  adapter: {seat.adapter}",
            f"  model: {_yaml_scalar(seat.model)}",
            f"  persona: {seat.persona}",
            "",
        ]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    config.path = target
    return target


def _yaml_scalar(value: str) -> str:
    return value if value else '""'
