"""Immutable chapter attempt history and its small, portable manifest contract."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

SCHEMA = "book-genesis.chapter-history/v1"


def manifest_path(project: Path, chapter: int) -> Path:
    return project / "manuscript" / "chapters" / "history" / f"chapter-{chapter:02d}" / "manifest.json"


def reserve_attempt(project: Path, chapter: int) -> tuple[str, int]:
    """Persist a pending id before any provider call, including legacy folders."""
    manifest = load_manifest(project, chapter)
    legacy = project / "manuscript" / "drafts" / f"chapter-{chapter:02d}" / "draft-1.md"
    sequence = max((int(item.get("sequence", 0)) for item in manifest["attempts"]), default=1 if legacy.exists() else 0) + 1
    attempt_id = f"attempt-{sequence:06d}"
    manifest["attempts"].append({"attempt_id": attempt_id, "sequence": sequence, "status": "pending"})
    write_manifest(project, chapter, manifest)
    return attempt_id, sequence


def next_attempt(project: Path, chapter: int) -> tuple[str, int]:
    """Backward-compatible alias; new callers should reserve before providers."""
    return reserve_attempt(project, chapter)


def load_manifest(project: Path, chapter: int) -> Dict[str, Any]:
    path = manifest_path(project, chapter)
    if not path.exists():
        return {"schema_version": SCHEMA, "chapter": chapter, "accepted": None, "attempts": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA or data.get("chapter") != chapter or not isinstance(data.get("attempts"), list):
        raise ValueError(f"invalid chapter history manifest: {path}")
    return data


def write_manifest(project: Path, chapter: int, manifest: Dict[str, Any]) -> None:
    path = manifest_path(project, chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_text(path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def record_draft(project: Path, chapter: int, attempt_id: str, path: Path) -> None:
    manifest = load_manifest(project, chapter)
    for item in manifest["attempts"]:
        if item.get("attempt_id") == attempt_id:
            item.update({"status": "drafted", "draft_path": project_relative(project, path), "sha256": sha256(path)})
            write_manifest(project, chapter, manifest)
            return
    raise ValueError(f"attempt not reserved: {attempt_id}")


def project_relative(project: Path, path: Path) -> str:
    root = project.resolve()
    resolved = path.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"history path escapes project: {path}") from exc


def draft_record(project: Path, path: Path, attempt_id: str, sequence: int, status: str = "drafted") -> Dict[str, Any]:
    return {"attempt_id": attempt_id, "sequence": sequence, "status": status, "draft_path": project_relative(project, path), "sha256": sha256(path)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)
