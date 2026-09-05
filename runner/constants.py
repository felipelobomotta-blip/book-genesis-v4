"""Genre constants and the role→model map, loaded from runner/config/*.yaml.

Prompts never restate these numbers; the runner injects them. That is what keeps
the twelve agent files from drifting apart again.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping

from runner.filesystem import load_simple_yaml_map

CONFIG_DIR = Path(__file__).resolve().parent / "config"
GENRE_PROFILES_PATH = CONFIG_DIR / "genre-profiles.yaml"
MODELS_PATH = CONFIG_DIR / "models.yaml"
ADAPTERS_PATH = CONFIG_DIR / "adapters.yaml"
USER_ADAPTERS_ENV = "BOOK_GENESIS_ADAPTERS"


def user_adapters_path() -> Path:
    """Where a person declares their own model CLI without editing the repository."""
    import os

    override = os.environ.get(USER_ADAPTERS_ENV, "")
    return Path(override) if override else Path.home() / ".book-genesis" / "adapters.yaml"


def load_generic_adapters() -> Dict[str, str]:
    """``{adapter name: command template}``: the repository's adapters.yaml, then the
    person's own ``~/.book-genesis/adapters.yaml`` on top (ADR 0010).

    Same shape as models.yaml versus ~/.book-genesis/config.yaml: a repository default that
    a person can extend or override without a fork and without a merge conflict on update.
    """
    templates: Dict[str, str] = {}
    for path in (ADAPTERS_PATH, user_adapters_path()):
        if not path.exists():
            continue
        for name, values in load_simple_yaml_map(path).items():
            command = str(values.get("command", "")).strip()
            if command:
                templates[name.strip().lower()] = command
    return templates


def load_generic_adapter_requirements() -> Dict[str, List[str]]:
    """Executables required by each declared CLI adapter.

    A bridge is itself run by Python, but Python being installed says nothing about
    the CLI wrapped by that bridge.  ``requires`` lets a declaration make that
    dependency explicit.  Older/user declarations without it retain the useful
    default of checking the command head itself.
    """
    requirements: Dict[str, List[str]] = {}
    for path in (ADAPTERS_PATH, user_adapters_path()):
        if not path.exists():
            continue
        for name, values in load_simple_yaml_map(path).items():
            normalized = name.strip().lower()
            declared = values.get("requires", [])
            if isinstance(declared, list):
                items = [str(item).strip() for item in declared]
            else:
                items = [part.strip() for part in str(declared).split(",")]
            requirements[normalized] = [item for item in items if item]
    return requirements

ROLES = ("writer", "disruptor", "judge", "editor", "architect", "extractor")


@dataclass(frozen=True)
class GenreProfile:
    key: str
    words_per_chapter_min: int
    words_per_chapter_max: int
    dialogue_min_pct: int
    dialogue_max_pct: int
    max_revision_cycles: int
    disruptor_default: bool
    ai_pattern_budget_per_1k: float


@dataclass(frozen=True)
class RoleModel:
    adapter: str
    model: str


@dataclass(frozen=True)
class PanelSpec:
    adapter: str
    model: str
    persona: str


DEFAULT_PERSONAS = (
    "the reader who buys this genre and has read the ten books everyone compares it to",
    "the hostile reader who did not want to read this and is looking for a reason to stop",
    "the casual reader who picked this up at an airport and will give it ten pages",
)


def load_panel() -> List[PanelSpec]:
    """Reader panel seats from models.yaml: every top-level entry whose key starts with ``panel``."""
    entries = load_simple_yaml_map(MODELS_PATH)
    panel: List[PanelSpec] = []
    for key, values in entries.items():
        if not key.startswith("panel"):
            continue
        panel.append(
            PanelSpec(
                adapter=str(values.get("adapter", "")).strip(),
                model=str(values.get("model", "")).strip(),
                persona=str(values.get("persona", "")).strip(),
            )
        )
    return panel


def load_genre_profile(genre: str) -> GenreProfile:
    entries = dict(load_simple_yaml_map(GENRE_PROFILES_PATH))
    aliases_raw = entries.pop("aliases", {})
    aliases = {str(key).lower(): str(value) for key, value in aliases_raw.items()}
    key = resolve_genre_key(genre, profiles=entries.keys(), aliases=aliases)
    return _profile_from(key, entries[key])


def resolve_genre_key(genre: str, *, profiles: Iterable[str], aliases: Mapping[str, str]) -> str:
    profile_keys = set(profiles)
    text = " ".join(genre.lower().replace("_", " ").replace("-", " ").replace("/", " ").split())
    if text in profile_keys:
        return text
    if text in aliases and aliases[text] in profile_keys:
        return aliases[text]
    words = set(text.split())
    candidates = sorted(list(profile_keys) + list(aliases), key=len, reverse=True)
    for candidate in candidates:
        if candidate == "default":
            continue
        if " " in candidate:
            matched = candidate in text
        else:
            matched = candidate in words
        if not matched:
            continue
        if candidate in profile_keys:
            return candidate
        target = aliases[candidate]
        if target in profile_keys:
            return target
    return "default"


def load_model_map() -> Dict[str, RoleModel]:
    entries = load_simple_yaml_map(MODELS_PATH)
    model_map: Dict[str, RoleModel] = {}
    for role, values in entries.items():
        if role.startswith("panel"):
            continue
        model_map[role] = RoleModel(
            adapter=str(values.get("adapter", "")).strip(),
            model=str(values.get("model", "")).strip(),
        )
    return model_map


def _profile_from(key: str, values: Mapping[str, object]) -> GenreProfile:
    return GenreProfile(
        key=key,
        words_per_chapter_min=int(str(values["words_per_chapter_min"])),
        words_per_chapter_max=int(str(values["words_per_chapter_max"])),
        dialogue_min_pct=int(str(values["dialogue_min_pct"])),
        dialogue_max_pct=int(str(values["dialogue_max_pct"])),
        max_revision_cycles=int(str(values["max_revision_cycles"])),
        disruptor_default=str(values["disruptor_default"]).strip().lower() in ("true", "yes", "1"),
        ai_pattern_budget_per_1k=float(str(values["ai_pattern_budget_per_1k"])),
    )
