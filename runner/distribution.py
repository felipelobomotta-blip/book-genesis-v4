from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
from typing import Mapping
from uuid import uuid4

from runner.filesystem import REPO_ROOT, load_manifest


DISTRIBUTION_MANIFEST_PATH = REPO_ROOT / "distribution" / "portable-suite.json"
INSTALL_RECORD = ".book-genesis-install.json"
BACKUP_DIRECTORY = ".book-genesis-backups"


def load_distribution_manifest() -> dict[str, object]:
    data = json.loads(DISTRIBUTION_MANIFEST_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported portable suite manifest version")
    return data


def supported_targets() -> tuple[str, ...]:
    targets = load_distribution_manifest().get("targets", {})
    if not isinstance(targets, dict):
        raise ValueError("Portable suite targets must be an object")
    return tuple(sorted(str(name) for name in targets))


def resolve_install_root(
    target: str,
    *,
    destination: str | Path | None = None,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    manifest = load_distribution_manifest()
    targets = manifest.get("targets", {})
    if not isinstance(targets, dict) or target not in targets:
        available = ", ".join(supported_targets())
        raise KeyError(f"Unknown install target {target!r}. Available targets: {available}")

    if destination is not None:
        return Path(destination).expanduser().resolve()

    spec = targets[target]
    if not isinstance(spec, dict):
        raise ValueError(f"Invalid install target definition for {target}")

    environment = os.environ if environ is None else environ
    home_env = str(spec.get("home_env", ""))
    configured_home = environment.get(home_env, "") if home_env else ""
    runtime_home = Path(configured_home).expanduser() if configured_home else (home or Path.home()) / str(
        spec["default_home"]
    )
    return (runtime_home / str(spec["skills_dir"])).resolve()


def selected_skills(*, include_legacy: bool = False) -> list[str]:
    manifest = load_distribution_manifest()
    skills = [str(name) for name in manifest.get("skills", [])]
    if include_legacy:
        skills.extend(str(name) for name in manifest.get("legacy_skills", []))
    return skills


def validate_suite() -> dict[str, object]:
    manifest = load_distribution_manifest()
    errors: list[str] = []
    warnings: list[str] = []

    canonical_skill = str(manifest.get("canonical_skill", ""))
    skills = selected_skills()
    if not canonical_skill:
        errors.append("canonical_skill is missing")
    elif canonical_skill not in skills:
        errors.append(f"canonical skill {canonical_skill!r} is not in portable skill list")

    if len(skills) != len(set(skills)):
        errors.append("portable skill list contains duplicates")

    for skill_name in skills:
        skill_file = REPO_ROOT / "skills" / skill_name / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"missing skill entrypoint: {skill_file.relative_to(REPO_ROOT).as_posix()}")
            continue
        frontmatter = _read_frontmatter(skill_file)
        if frontmatter.get("name") != skill_name:
            errors.append(f"skill name mismatch in {skill_file.relative_to(REPO_ROOT).as_posix()}")
        if not frontmatter.get("description"):
            errors.append(f"skill description missing in {skill_file.relative_to(REPO_ROOT).as_posix()}")

    registry_value = str(manifest.get("agent_registry", ""))
    registry_path = REPO_ROOT / registry_value
    if not registry_path.exists():
        errors.append(f"agent registry missing: {registry_value}")
    else:
        registry_text = registry_path.read_text(encoding="utf-8")
        for referenced in re.findall(r'^\s*skill:\s*"([^"]+)"', registry_text, flags=re.MULTILINE):
            referenced_path = REPO_ROOT / referenced
            if not referenced_path.exists():
                errors.append(f"agent registry references missing file: {referenced}")
            if referenced.startswith("skills/"):
                dependency = referenced.split("/", 2)[1]
                if dependency not in skills:
                    errors.append(f"agent registry dependency is not packaged: {dependency}")

    canonical_root = REPO_ROOT / "skills" / canonical_skill
    phases = load_manifest()
    labels = {phase.label for phase in phases}
    gates = [phase.gate for phase in phases]
    if len(gates) != len(set(gates)):
        errors.append("canonical pipeline contains duplicate gates")
    if "Phase 4: Adversarial Audit" not in labels:
        errors.append("canonical pipeline is missing mandatory adversarial audit")
    if "Phase 5: Literary Barrier Revision Loop" not in labels:
        errors.append("canonical pipeline is missing literary barrier revision loop")
    for phase in phases:
        prompt_path = canonical_root / phase.prompt
        if not prompt_path.exists():
            errors.append(f"phase prompt missing: {phase.prompt}")
        for reference in phase.references:
            reference_path = canonical_root / reference
            if not reference_path.exists():
                errors.append(f"phase reference missing: {reference}")
        if phase.next and phase.next not in labels:
            errors.append(f"phase {phase.label!r} points to unknown next phase {phase.next!r}")

    evaluator_protocol = canonical_root / "references" / "scoring" / "evaluator-protocol.md"
    if not evaluator_protocol.exists():
        errors.append("independent evaluator protocol is missing")

    required_targets = {"claude", "codex", "kimi", "shared"}
    target_names = set(supported_targets())
    missing_targets = sorted(required_targets - target_names)
    if missing_targets:
        errors.append(f"portable targets missing: {', '.join(missing_targets)}")

    legacy = [str(name) for name in manifest.get("legacy_skills", [])]
    overlap = sorted(set(skills) & set(legacy))
    if overlap:
        warnings.append(f"legacy skills also included in portable profile: {', '.join(overlap)}")

    legacy_claude = manifest.get("legacy_claude", {})
    if not isinstance(legacy_claude, dict):
        errors.append("legacy_claude must be an object")
    else:
        for key in ("agents_dir", "knowledge_dir"):
            source_dir = REPO_ROOT / str(legacy_claude.get(key, ""))
            if not source_dir.is_dir():
                errors.append(f"legacy Claude source directory missing: {source_dir.name}")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def install_suite(
    target: str,
    *,
    destination: str | Path | None = None,
    include_legacy: bool = False,
    force: bool = False,
    dry_run: bool = False,
    home: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    validation = validate_suite()
    if not validation["ok"]:
        return {
            "ok": False,
            "destination": "",
            "actions": [],
            "legacy_actions": [],
            "conflicts": [],
            "errors": list(validation["errors"]),
        }

    destination_root = resolve_install_root(
        target,
        destination=destination,
        home=home,
        environ=environ,
    )
    source_root = (REPO_ROOT / "skills").resolve()
    if destination_root == source_root:
        return {
            "ok": False,
            "destination": str(destination_root),
            "actions": [],
            "legacy_actions": [],
            "conflicts": [],
            "errors": ["installation destination cannot be repository source skills directory"],
        }
    if destination_root.exists() and not destination_root.is_dir():
        return {
            "ok": False,
            "destination": str(destination_root),
            "actions": [],
            "legacy_actions": [],
            "conflicts": [],
            "errors": ["installation destination exists and is not a directory"],
        }

    actions: list[dict[str, str]] = []
    conflicts: list[str] = []
    skills = selected_skills(include_legacy=include_legacy)
    missing_sources = [skill_name for skill_name in skills if not (source_root / skill_name / "SKILL.md").exists()]
    if missing_sources:
        return {
            "ok": False,
            "destination": str(destination_root),
            "actions": [],
            "legacy_actions": [],
            "conflicts": [],
            "errors": [f"source skills missing: {', '.join(missing_sources)}"],
        }

    for skill_name in skills:
        source = source_root / skill_name
        destination_skill = destination_root / skill_name
        if not destination_skill.exists():
            action = "install"
        elif destination_skill.is_dir() and _tree_digest(source) == _tree_digest(destination_skill):
            action = "unchanged"
        elif force:
            action = "replace"
        else:
            action = "conflict"
            conflicts.append(skill_name)
        actions.append({"skill": skill_name, "action": action, "destination": str(destination_skill)})

    legacy_actions = _plan_legacy_claude_files(
        target=target,
        include_legacy=include_legacy,
        destination_root=destination_root,
        force=force,
    )
    for item in legacy_actions:
        if item["action"] == "conflict":
            conflicts.append(f"{item['component']}/{item['name']}")

    if conflicts:
        return {
            "ok": False,
            "destination": str(destination_root),
            "actions": actions,
            "legacy_actions": legacy_actions,
            "conflicts": conflicts,
            "errors": ["existing skill directories differ; rerun with --force to back them up and replace them"],
        }

    if dry_run:
        return {
            "ok": True,
            "destination": str(destination_root),
            "actions": actions,
            "legacy_actions": legacy_actions,
            "conflicts": [],
            "errors": [],
            "dry_run": True,
        }

    destination_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_root: Path | None = None

    for item in actions:
        if item["action"] == "unchanged":
            continue
        skill_name = item["skill"]
        source = source_root / skill_name
        destination_skill = destination_root / skill_name
        stage_root = destination_root / f".book-genesis-stage-{uuid4().hex}"
        stage_skill = stage_root / skill_name
        previous_backup: Path | None = None
        try:
            shutil.copytree(source, stage_skill)
            if destination_skill.exists():
                backup_root = destination_root / BACKUP_DIRECTORY / timestamp
                backup_root.mkdir(parents=True, exist_ok=True)
                previous_backup = backup_root / skill_name
                destination_skill.rename(previous_backup)
            stage_skill.rename(destination_skill)
        except Exception:
            if previous_backup is not None and previous_backup.exists() and not destination_skill.exists():
                previous_backup.rename(destination_skill)
            raise
        finally:
            shutil.rmtree(stage_root, ignore_errors=True)

    for item in legacy_actions:
        if item["action"] == "unchanged":
            continue
        source = Path(item["source"])
        destination_file = Path(item["destination"])
        stage_root = destination_root / f".book-genesis-stage-{uuid4().hex}"
        stage_file = stage_root / item["component"] / item["name"]
        previous_backup: Path | None = None
        try:
            stage_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, stage_file)
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            if destination_file.exists():
                backup_root = destination_root / BACKUP_DIRECTORY / timestamp
                previous_backup = backup_root / item["component"] / item["name"]
                previous_backup.parent.mkdir(parents=True, exist_ok=True)
                destination_file.rename(previous_backup)
            stage_file.rename(destination_file)
        except Exception:
            if previous_backup is not None and previous_backup.exists() and not destination_file.exists():
                previous_backup.rename(destination_file)
            raise
        finally:
            shutil.rmtree(stage_root, ignore_errors=True)

    installed = {
        item["skill"]: _tree_digest(destination_root / item["skill"])
        for item in actions
    }
    record = {
        "schema_version": 1,
        "suite": load_distribution_manifest()["suite_name"],
        "target": target,
        "canonical_skill": load_distribution_manifest()["canonical_skill"],
        "include_legacy": include_legacy,
        "installed_at_utc": datetime.now(timezone.utc).isoformat(),
        "skills": installed,
        "legacy_claude_files": {
            f"{item['component']}/{item['name']}": _file_digest(Path(item["destination"]))
            for item in legacy_actions
        },
    }
    (destination_root / INSTALL_RECORD).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "destination": str(destination_root),
        "actions": actions,
        "legacy_actions": legacy_actions,
        "conflicts": [],
        "errors": [],
        "dry_run": False,
        "backup": str(backup_root) if backup_root else "",
    }


def _read_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return {}


def _plan_legacy_claude_files(
    *,
    target: str,
    include_legacy: bool,
    destination_root: Path,
    force: bool,
) -> list[dict[str, str]]:
    if target != "claude" or not include_legacy:
        return []

    manifest = load_distribution_manifest()
    legacy = manifest.get("legacy_claude", {})
    if not isinstance(legacy, dict):
        return []

    runtime_root = destination_root.parent
    collections = (
        ("agents", REPO_ROOT / str(legacy["agents_dir"]), runtime_root / "agents"),
        ("knowledge", REPO_ROOT / str(legacy["knowledge_dir"]), runtime_root / "knowledge"),
    )
    actions: list[dict[str, str]] = []
    for component, source_dir, destination_dir in collections:
        for source in sorted(source_dir.glob("*.md")):
            destination_file = destination_dir / source.name
            if not destination_file.exists():
                action = "install"
            elif destination_file.is_file() and _file_digest(source) == _file_digest(destination_file):
                action = "unchanged"
            elif force:
                action = "replace"
            else:
                action = "conflict"
            actions.append(
                {
                    "component": component,
                    "name": source.name,
                    "action": action,
                    "source": str(source),
                    "destination": str(destination_file),
                }
            )
    return actions


def _file_digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _tree_digest(root: Path) -> str:
    digest = sha256()
    if not root.is_dir():
        return ""
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()
