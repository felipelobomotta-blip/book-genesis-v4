from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import re
from pathlib import Path
from typing import Dict, List


from runner.resources import resource_root

REPO_ROOT = resource_root()
SKILL_ROOT = REPO_ROOT / "skills" / "book-genesis-codex"
MANIFEST_PATH = SKILL_ROOT / "references" / "pipeline" / "manifest.yaml"


@dataclass(frozen=True)
class Phase:
    key: str
    label: str
    prompt: str
    gate: str
    outputs: List[str]
    next: str


@dataclass(frozen=True)
class AgentSpec:
    key: str
    label: str
    skill: str
    mission: str
    timing: str
    inputs: List[str]
    outputs: List[str]
    gates: List[str]
    score_floor: str


ARTIFACT_HEADINGS: Dict[str, str] = {
    "00-brief.md": "Brief",
    "01-market-map.md": "Market Map",
    "02-story-engine.md": "Story Engine",
    "03-characters.md": "Characters",
    "04-theme.md": "Theme",
    "05-outline.md": "Outline",
    "06-emotional-curve.md": "Emotional Curve",
    "07-opening-strategy.md": "Opening Strategy",
    "08-adversarial-audit.md": "Adversarial Audit",
    "09-genesis-score-codex.md": "Genesis Score",
    "10-editorial-package.md": "Editorial Package",
}

BESTSELLER_STUDIO_ROOT = REPO_ROOT / "skills" / "book-bestseller-studio"
AGENT_REGISTRY_PATH = BESTSELLER_STUDIO_ROOT / "references" / "agent-registry.yaml"


def load_manifest() -> List[Phase]:
    entries = _load_simple_yaml_map(MANIFEST_PATH)
    return [
        Phase(
            key=key,
            label=str(entry.get("label", "")),
            prompt=str(entry.get("prompt", "")),
            gate=str(entry.get("gate", "")),
            outputs=list(entry.get("outputs", [])),
            next=str(entry.get("next", "")),
        )
        for key, entry in entries.items()
    ]


def load_agent_registry() -> List[AgentSpec]:
    entries = _load_simple_yaml_map(AGENT_REGISTRY_PATH)
    return [
        AgentSpec(
            key=key,
            label=str(entry.get("label", "")),
            skill=str(entry.get("skill", "")),
            mission=str(entry.get("mission", "")),
            timing=str(entry.get("timing", "")),
            inputs=list(entry.get("inputs", [])),
            outputs=list(entry.get("outputs", [])),
            gates=list(entry.get("gates", [])),
            score_floor=str(entry.get("score_floor", "")),
        )
        for key, entry in entries.items()
    ]


def get_agent_spec(agent_key: str) -> AgentSpec:
    normalized = _slugify(agent_key).replace("-", "_")
    for agent in load_agent_registry():
        if agent.key == agent_key or agent.key == normalized or _slugify(agent.label) == _slugify(agent_key):
            return agent
    available = ", ".join(agent.key for agent in load_agent_registry())
    raise KeyError(f"Unknown agent {agent_key!r}. Available agents: {available}")


def scaffold_project(
    target: Path,
    *,
    idea: str,
    adapter: str,
    model_name: str,
    language: str = "",
    force: bool = False,
) -> None:
    if (target / "PROJECT_STATE.yaml").exists() and not force:
        raise FileExistsError(f"{target} already contains PROJECT_STATE.yaml")

    phases = load_manifest()
    first_phase = phases[0]
    gates = "\n".join(f'  {phase.gate}: "pending"' for phase in phases)

    target.mkdir(parents=True, exist_ok=True)
    (target / "artifacts").mkdir(exist_ok=True)
    (target / "manuscript" / "chapters").mkdir(parents=True, exist_ok=True)
    (target / "evaluations").mkdir(exist_ok=True)
    (target / "delivery").mkdir(exist_ok=True)
    (target / "work").mkdir(exist_ok=True)

    write_if_needed(
        target / "PROJECT_STATE.yaml",
        _project_state_template(
            idea=idea,
            adapter=adapter,
            model_name=model_name,
            language=language,
            first_phase=first_phase.label,
            gates=gates,
        ),
        force=force,
    )
    write_if_needed(target / "ASSUMPTIONS.md", assumptions_template(idea), force=force)
    write_if_needed(target / "RUN_REPORT.md", run_report_template(), force=force)

    for phase in phases:
        for output in phase.outputs:
            if output.startswith("artifacts/"):
                path = target / output
                write_if_needed(path, artifact_template(Path(output).name), force=force)


def validate_project(target: Path) -> Dict[str, object]:
    required = [
        target / "PROJECT_STATE.yaml",
        target / "ASSUMPTIONS.md",
        target / "RUN_REPORT.md",
        target / "artifacts",
        target / "manuscript" / "chapters",
        target / "evaluations",
        target / "delivery",
    ]
    missing = [str(path) for path in required if not path.exists()]
    return {"ok": not missing, "missing": missing}


def load_state_summary(target: Path) -> Dict[str, str]:
    text = (target / "PROJECT_STATE.yaml").read_text(encoding="utf-8")
    return {
        "title": _extract_scalar(text, "title"),
        "idea": _extract_scalar(text, "idea"),
        "language": _extract_scalar(text, "language"),
        "genre": _extract_scalar(text, "genre"),
        "audience": _extract_scalar(text, "audience"),
        "adapter": _extract_scalar(text, "adapter"),
        "model_name": _extract_scalar(text, "model_name"),
        "current_phase": _extract_scalar(text, "current_phase"),
        "status": _extract_scalar(text, "status"),
    }


def prepare_phase(target: Path) -> Path:
    phase = current_phase(target)
    prompt_path = SKILL_ROOT / phase.prompt
    prompt_text = prompt_path.read_text(encoding="utf-8")
    output_list = "\n".join(f"- {item}" for item in phase.outputs)

    packet = (
        f"# Current Phase\n\n"
        f"- Label: {phase.label}\n"
        f"- Gate: {phase.gate}\n"
        f"- Prompt: {phase.prompt}\n"
        f"- Required outputs:\n{output_list}\n\n"
        f"## Phase Prompt\n\n"
        f"{prompt_text.rstrip()}\n"
    )

    work_dir = target / "work"
    work_dir.mkdir(exist_ok=True)
    packet_path = work_dir / "current-phase.md"
    packet_path.write_text(packet, encoding="utf-8")
    _update_state_value(target / "PROJECT_STATE.yaml", "current_gate", phase.gate)
    _update_state_value(target / "PROJECT_STATE.yaml", "status", "in_progress")
    return packet_path


def prepare_swarm_run(
    target: Path,
    *,
    slug: str = "reader-swarm",
    mode: str = "hybrid",
    run_date: str = "",
) -> Path:
    run_slug = _slugify(slug or mode or "reader-swarm")
    run_id = f"{run_date or date.today().isoformat()}-{run_slug}"
    run_dir = target / "evaluations" / "book-swarm" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    chapters_dir = target / "manuscript" / "chapters"
    chapters = sorted(chapters_dir.glob("*.md")) if chapters_dir.exists() else []
    chapter_lines = "\n".join(f"- `{chapter.relative_to(target).as_posix()}`" for chapter in chapters)
    if not chapter_lines:
        chapter_lines = "- No chapter files found yet."

    files = {
        "persona-roster.json": json.dumps(
            {
                "mode": mode,
                "run_slug": run_slug,
                "personas": [],
                "note": "Fill with fictional diagnostic personas before running cohort reports.",
            },
            indent=2,
        )
        + "\n",
        "sample-map.md": (
            "# Sample Map\n\n"
            f"- Mode: `{mode}`\n"
            f"- Run slug: `{run_slug}`\n\n"
            "## Available Manuscript Files\n\n"
            f"{chapter_lines}\n\n"
            "## Required Coverage\n\n"
            "- First chapter\n"
            "- Final chapter if available\n"
            "- Climax or strongest tension sample\n"
            "- Weakest flagged chapters\n"
            "- Strongest flagged chapters\n"
        ),
        "cohort-reports.md": swarm_template("Cohort Reports"),
        "interviews.md": swarm_template("Interviews"),
        "public-opinion-report.md": swarm_template("Public Opinion Report"),
        "risk-heatmap.md": (
            "# Risk Heatmap\n\n"
            "| Area | Chapter/Asset | Cohort | Severity | Evidence | Fix Type | Owner |\n"
            "|---|---|---|---|---|---|---|\n"
        ),
        "revision-tickets.md": swarm_template("Revision Tickets"),
        "score-calibration.md": (
            "# Score Calibration\n\n"
            "Raw swarm score:\n"
            "Calibrated score:\n"
            "Confidence:\n"
            "Coverage:\n"
            "Weakest cohort:\n"
            "Best cohort:\n"
            "Human validation still needed:\n"
        ),
        "mirofish-requirement.md": (
            "# MiroFish Requirement\n\n"
            "Use this only when an external MiroFish project/server is available.\n\n"
            "## Seed Inputs\n\n"
            "- Manuscript/package files listed in `sample-map.md`\n"
            "- Persona roster from `persona-roster.json`\n\n"
            "## Import Contract\n\n"
            "- Persona files\n"
            "- Action logs\n"
            "- Interviews\n"
            "- Summary report\n\n"
            "Do not copy AGPL MiroFish code into this repository.\n"
        ),
        "SUMMARY.md": swarm_template("Summary"),
    }

    for filename, content in files.items():
        write_if_needed(run_dir / filename, content, force=False)

    return run_dir


def prepare_agent_packet(target: Path, agent_key: str) -> Path:
    agent = get_agent_spec(agent_key)
    packet_dir = target / "work" / "agent-packets"
    packet_dir.mkdir(parents=True, exist_ok=True)

    input_lines = _path_status_lines(target, agent.inputs)
    output_lines = "\n".join(f"- `{item}`" for item in agent.outputs) or "- No required outputs listed."
    gate_lines = "\n".join(f"- {item}" for item in agent.gates) or "- No gates listed."

    skill_path = REPO_ROOT / agent.skill
    skill_excerpt = ""
    if skill_path.exists():
        skill_excerpt = skill_path.read_text(encoding="utf-8").strip()
    else:
        skill_excerpt = f"Skill file not found: `{agent.skill}`"

    packet = (
        f"# Agent Packet: {agent.label}\n\n"
        f"- Agent key: `{agent.key}`\n"
        f"- Timing: {agent.timing}\n"
        f"- Score floor: {agent.score_floor or 'project default'}\n"
        f"- Skill: `{agent.skill}`\n\n"
        "## Mission\n\n"
        f"{agent.mission}\n\n"
        "## Input Status\n\n"
        f"{input_lines}\n\n"
        "## Required Outputs\n\n"
        f"{output_lines}\n\n"
        "## Gates\n\n"
        f"{gate_lines}\n\n"
        "## Operating Rule\n\n"
        "Produce durable files only. Passing internal gates is not evidence of market success, virality, or a calibrated literary score. "
        "When a gate fails, write blockers and revision tickets instead of inflating scores.\n\n"
        "## Skill Prompt\n\n"
        f"{skill_excerpt}\n"
    )

    packet_path = packet_dir / f"{agent.key}.md"
    packet_path.write_text(packet, encoding="utf-8")
    return packet_path


def advance_phase(target: Path) -> Dict[str, object]:
    phase = current_phase(target)
    pending = pending_outputs(target, phase.outputs)
    if pending:
        return {"ok": False, "pending": pending, "next_phase": phase.label}

    if phase.label == "Phase 4: Adversarial Audit":
        from runner.audit import audit_status
        try:
            status = audit_status((target / "artifacts" / "08-adversarial-audit.md").read_text(encoding="utf-8"))
        except ValueError as exc:
            return {"ok": False, "pending": [str(exc)], "next_phase": phase.label}
        if status != "pass":
            state = target / "PROJECT_STATE.yaml"
            _update_state_value(state, phase.gate, "blocked")
            _update_state_value(state, "current_phase", phase.label)
            _update_state_value(state, "current_gate", phase.gate)
            _update_state_value(state, "status", "awaiting_revision")
            return {"ok": False, "pending": [f"audit_status: {status}"], "next_phase": phase.label}

    state = target / "PROJECT_STATE.yaml"
    _update_state_value(state, phase.gate, "passed")

    if phase.next:
        _update_state_value(state, "current_phase", phase.next)
        _update_state_value(state, "current_gate", "")
        _update_state_value(state, "status", "ready")
    else:
        _update_state_value(state, "status", "completed")
        _update_state_value(state, "current_gate", "")

    return {"ok": True, "pending": [], "next_phase": phase.next or "completed"}


def create_demo(target: Path, *, adapter: str, model_name: str) -> None:
    scaffold_project(
        target,
        idea="Mechanical smoke-test novella about an archivist who audits a haunted manuscript.",
        adapter=adapter,
        model_name=model_name,
        language="en",
        force=True,
    )

    while load_state_summary(target)["status"] != "completed":
        phase = current_phase(target)
        fill_outputs_for_demo(target, phase)
        result = advance_phase(target)
        if not result["ok"]:
            raise RuntimeError(f"Demo could not advance: {result['pending']}")

    (target / "RUN_REPORT.md").write_text(
        "# Run Report\n\n"
        "## Run Summary\n\n"
        "This is a deterministic mechanical demo. It proves the file workflow, gates, "
        "and phase advancement, not literary quality.\n\n"
        "## Result\n\n"
        "- Status: completed\n"
        "- Chapters: 2 demo chapters\n",
        encoding="utf-8",
    )


def current_phase(target: Path) -> Phase:
    label = load_state_summary(target)["current_phase"]
    for phase in load_manifest():
        if phase.label == label:
            return phase
    raise KeyError(f"Unknown current phase: {label}")


def pending_outputs(target: Path, outputs: List[str]) -> List[str]:
    pending: List[str] = []
    for output in outputs:
        path = target / output
        if output == "manuscript/chapters":
            chapters = list(path.glob("chapter-*.md")) if path.exists() else []
            outline = target / "artifacts" / "05-outline.md"
            expected = _outline_chapter_numbers(outline.read_text(encoding="utf-8")) if outline.exists() else []
            actual = sorted(int(match.group(1)) for item in chapters if (match := re.fullmatch(r"chapter-(\d+)\.md", item.name)))
            if not expected or actual != expected:
                pending.append(output)
            continue
        if not path.exists():
            pending.append(output)
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text or "BOOK_GENESIS_TEMPLATE" in text or text == template_for_output(output).strip():
            pending.append(output)
    return pending


def _outline_chapter_numbers(outline: str) -> List[int]:
    marker = re.compile(r"^\s*(?:#{1,6}\s*|\*\*\s*)(?:chapter|cap[ií]tulo|cap\.?)\s*0*(\d+)\b", re.IGNORECASE)
    numbers = [int(match.group(1)) for line in outline.splitlines() if (match := marker.match(line))]
    expected = list(range(1, max(numbers) + 1)) if numbers else []
    return expected if sorted(numbers) == expected else []


def fill_outputs_for_demo(target: Path, phase: Phase) -> None:
    for output in phase.outputs:
        path = target / output
        if output == "manuscript/chapters":
            chapters_dir = target / "manuscript" / "chapters"
            chapters_dir.mkdir(parents=True, exist_ok=True)
            (chapters_dir / "chapter-01.md").write_text(
                "# Chapter 1\n\nThe archivist found the same sentence written in three hands.\n",
                encoding="utf-8",
            )
            (chapters_dir / "chapter-02.md").write_text(
                "# Chapter 2\n\nBy dawn, the audit log had started correcting him back.\n",
                encoding="utf-8",
            )
            continue
        if output == "artifacts/05-outline.md":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Demo Outline\n\n## Chapter 1: The Archive\n\nA beginning.\n\n## Chapter 2: The Audit\n\nAn ending.\n",
                encoding="utf-8",
            )
            continue
        if output == "artifacts/08-adversarial-audit.md":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Demo Audit\n\nMechanical demonstration only; no literary assessment.\n\naudit_status: pass\n",
                encoding="utf-8",
            )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# Demo Output: {phase.label}\n\n"
            f"Generated for `{output}` by the mechanical demo runner.\n\n"
            "This content is intentionally short. It exists to prove the workflow contract.\n",
            encoding="utf-8",
        )


def template_for_output(output: str) -> str:
    if output == "ASSUMPTIONS.md":
        return assumptions_template("")
    if output.startswith("artifacts/"):
        return artifact_template(Path(output).name)
    return ""


def artifact_template(filename: str) -> str:
    heading = ARTIFACT_HEADINGS.get(filename, filename)
    return (
        f"# {heading}\n\n"
        "<!-- BOOK_GENESIS_TEMPLATE: replace this file with phase output. -->\n\n"
        "## Required Content\n\n"
        "- Fill this artifact from the active phase prompt.\n"
        "- Cite assumptions and evidence where applicable.\n"
    )


def assumptions_template(idea: str) -> str:
    idea_line = f"\nUser idea: {idea}\n" if idea else ""
    return (
        "# Assumptions\n"
        f"{idea_line}\n"
        "<!-- BOOK_GENESIS_TEMPLATE: replace inferred assumptions before advancing. -->\n\n"
        "## Confirmed Inputs\n\n"
        "- TBD\n\n"
        "## Inferred Assumptions\n\n"
        "- TBD\n\n"
        "## Open Questions\n\n"
        "- TBD\n"
    )


def run_report_template() -> str:
    return (
        "# Run Report\n\n"
        "## Run Summary\n\n"
        "<!-- BOOK_GENESIS_TEMPLATE: update as phases complete. -->\n\n"
        "## Phase Log\n\n"
        "- TBD\n"
    )


def swarm_template(title: str) -> str:
    return (
        f"# {title}\n\n"
        "<!-- BOOK_SWARM_TEMPLATE: replace with simulated reader evidence or imported MiroFish output. -->\n\n"
        "## Required Content\n\n"
        "- Evidence-backed findings.\n"
        "- Clear simulated-signal vs editorial-judgment labels.\n"
        "- Human validation needs where applicable.\n"
    )


def write_if_needed(path: Path, content: str, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return
    path.write_text(content, encoding="utf-8")


def _project_state_template(
    *,
    idea: str,
    adapter: str,
    model_name: str,
    language: str,
    first_phase: str,
    gates: str,
) -> str:
    return (
        "project:\n"
        "  id: \"\"\n"
        "  title: \"\"\n"
        f"  idea: \"{_escape_yaml(idea)}\"\n"
        f"  language: \"{_escape_yaml(language)}\"\n"
        "  genre: \"\"\n"
        "  audience: \"\"\n"
        "  target_length: \"\"\n\n"
        "runtime:\n"
        f"  adapter: \"{_escape_yaml(adapter)}\"\n"
        f"  model_family: \"{_infer_family(model_name)}\"\n"
        f"  model_name: \"{_escape_yaml(model_name)}\"\n\n"
        "pipeline:\n"
        f"  current_phase: \"{first_phase}\"\n"
        "  current_gate: \"\"\n"
        "  status: \"not_started\"\n"
        "  revision_iteration: 0\n\n"
        "artifacts:\n"
        "  generated: []\n\n"
        "manuscript:\n"
        "  chapter_count: 0\n"
        "  completed_chapters: []\n"
        "  status: \"not_started\"\n\n"
        "gates:\n"
        f"{gates}\n"
    )


def update_state_value(path: Path, key: str, value: str) -> None:
    """Public entry point: set the first ``key:`` scalar found in PROJECT_STATE.yaml."""
    _update_state_value(path, key, value.replace('"', "'"))


def _update_state_value(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    prefix = f"{key}:"
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(prefix):
            indent = line[: len(line) - len(line.lstrip())]
            lines[index] = f'{indent}{key}: "{value}"'
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise KeyError(f"Could not update key {key!r} in {path}")


def _extract_scalar(text: str, key: str) -> str:
    prefix = f"{key}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return _unquote(stripped.split(":", 1)[1].strip())
    return ""


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _escape_yaml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _infer_family(model_name: str) -> str:
    normalized = model_name.lower()
    if "claude" in normalized or "opus" in normalized or "sonnet" in normalized:
        return "claude"
    if "gpt" in normalized or "codex" in normalized:
        return "openai"
    if "gemini" in normalized:
        return "google"
    if "kimi" in normalized:
        return "kimi"
    return "unknown"


def load_simple_yaml_map(path: Path) -> Dict[str, Dict[str, object]]:
    """Public entry point for the two-level YAML subset used by manifests and config."""
    return _load_simple_yaml_map(path)


def _load_simple_yaml_map(path: Path) -> Dict[str, Dict[str, object]]:
    raw = path.read_text(encoding="utf-8").splitlines()
    entries: Dict[str, Dict[str, object]] = {}
    current_key = ""
    current_list_key = ""
    last_scalar_key = ""
    last_scalar_indent = -1

    for line in raw:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            current_key = line.split(":", 1)[0].strip()
            entries[current_key] = {}
            current_list_key = ""
            last_scalar_key = ""
            last_scalar_indent = -1
            continue
        if not current_key:
            raise ValueError(f"Value before top-level key in {path}: {line}")
        stripped = line.strip()
        if last_scalar_key and indent > last_scalar_indent:
            # A YAML plain-scalar folded onto a continuation line (deeper indent, no key of
            # its own): a real YAML writer wraps long values this way; join it back with a space.
            entries[current_key][last_scalar_key] = f"{entries[current_key][last_scalar_key]} {stripped}".strip()  # type: ignore[index]
            continue
        if stripped.startswith("- "):
            if not current_list_key:
                raise ValueError(f"List item without list key in {path}: {line}")
            entries[current_key].setdefault(current_list_key, [])
            entries[current_key][current_list_key].append(_unquote(stripped[2:].strip()))  # type: ignore[index]
            last_scalar_key = ""
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            entries[current_key][key] = []
            current_list_key = key
            last_scalar_key = ""
        else:
            entries[current_key][key] = _unquote(value)
            current_list_key = ""
            last_scalar_key = key
            last_scalar_indent = indent

    return entries


def _path_status_lines(target: Path, paths: List[str]) -> str:
    if not paths:
        return "- No required inputs listed."
    lines = []
    for item in paths:
        path = target / item
        status = "present" if path.exists() else "missing"
        lines.append(f"- `{item}`: {status}")
    return "\n".join(lines)


def _slugify(value: str) -> str:
    cleaned = []
    previous_dash = False
    for character in value.lower():
        if character.isalnum():
            cleaned.append(character)
            previous_dash = False
            continue
        if not previous_dash:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-") or "reader-swarm"
