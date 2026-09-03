"""Build the adapter for each role from runner/config/models.yaml (or a fake for tests)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from runner.adapters import Adapter, AdapterError, ClaudeCliAdapter, CodexCliAdapter, FakeAdapter
from runner.constants import ROLES, load_model_map

FAKE_SEPARATOR = "=== NEXT ==="


def load_fake_responses(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    parts = [part.strip("\r\n") for part in text.split(FAKE_SEPARATOR)]
    return [part for part in parts if part.strip()]


def build_adapter(name: str, *, fake_responses: Optional[List[str]] = None) -> Adapter:
    normalized = name.strip().lower()
    if normalized == "fake":
        return FakeAdapter(fake_responses or [])
    if normalized == "claude":
        return ClaudeCliAdapter()
    if normalized == "codex":
        return CodexCliAdapter()
    if normalized == "manual":
        raise AdapterError("the manual adapter is not available yet; use claude, codex, or fake")
    raise AdapterError(f"unknown adapter {name!r}; use claude, codex, or fake")


def build_role_adapters(*, fake_responses_path: Optional[Path] = None) -> Tuple[Dict[str, Adapter], Dict[str, str]]:
    """One adapter per role plus the model name per role.

    With ``fake_responses_path`` every role shares a single scripted adapter, so the
    responses are consumed in call order (writer, disruptor, judge, editor, judge...).
    """
    if fake_responses_path is not None:
        shared = FakeAdapter(load_fake_responses(fake_responses_path))
        return {role: shared for role in ROLES}, {role: "" for role in ROLES}

    model_map = load_model_map()
    cache: Dict[str, Adapter] = {}
    adapters: Dict[str, Adapter] = {}
    models: Dict[str, str] = {}
    for role, role_model in model_map.items():
        if role_model.adapter not in cache:
            cache[role_model.adapter] = build_adapter(role_model.adapter)
        adapters[role] = cache[role_model.adapter]
        models[role] = role_model.model
    return adapters, models
