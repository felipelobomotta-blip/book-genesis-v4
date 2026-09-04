"""Phases run by the runner, not by an agent with tools.

For every phase except drafting (which is chapter by chapter, see ``runner.book``),
the runner builds one prompt from the phase's reference prompt plus the project's
current artifacts, sends it through the architect role's adapter, splits the reply
into the required files, applies the state block, and advances only when every
required output exists (ADR 0001, decision 1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Dict, List, Tuple

from runner.adapters import Adapter
from runner.chapter import RUNNER_CONTRACT
from runner.filesystem import (
    ARTIFACT_HEADINGS,
    SKILL_ROOT,
    Phase,
    advance_phase,
    current_phase,
    load_state_summary,
    pending_outputs,
    update_state_value,
)

DRAFTING_LABEL = "Phase 3: Drafting"
PHASE_ROLE = "architect"
STATE_KEYS = ("title", "genre", "audience", "language", "target_length")
TEMPLATE_MARK = "BOOK_GENESIS_TEMPLATE"

_FILE_MARK = re.compile(r"^=== FILE:\s*(.+?)\s*===\s*$", re.MULTILINE)
_STATE_MARK = re.compile(r"^=== STATE ===\s*$", re.MULTILINE)
_FENCE = re.compile(r"^```[a-zA-Z]*[ \t]*\r?\n(.*?)\r?\n```\s*$", re.DOTALL)


@dataclass
class PhaseRunResult:
    ok: bool
    phase: str
    written: List[str] = field(default_factory=list)
    pending: List[str] = field(default_factory=list)
    ignored: List[str] = field(default_factory=list)
    next_phase: str = ""


def run_phase(
    project: Path,
    adapters: Dict[str, Adapter],
    models: Dict[str, str],
    *,
    role: str = PHASE_ROLE,
) -> PhaseRunResult:
    phase = current_phase(project)
    if phase.label == DRAFTING_LABEL:
        raise ValueError("Phase 3 (drafting) runs chapter by chapter: use `book` or `chapter`, not `run-phase`")

    prompt = build_phase_prompt(project, phase)
    response = adapters[role].complete(prompt, model=models.get(role, ""))
    files, state = split_files(response)

    required = [output for output in phase.outputs if output != "manuscript/chapters"]
    written: List[str] = []
    ignored: List[str] = []
    for relative, content in files.items():
        if relative not in required:
            ignored.append(relative)
            continue
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(relative)

    state_path = project / "PROJECT_STATE.yaml"
    for key, value in state.items():
        if key in STATE_KEYS and value:
            update_state_value(state_path, key, value)

    pending = pending_outputs(project, phase.outputs)
    if pending:
        return PhaseRunResult(False, phase.label, written, pending, ignored, phase.label)
    advanced = advance_phase(project)
    return PhaseRunResult(
        bool(advanced["ok"]),
        phase.label,
        written,
        list(advanced.get("pending", [])),
        ignored,
        str(advanced["next_phase"]),
    )


def build_phase_prompt(project: Path, phase: Phase) -> str:
    summary = load_state_summary(project)
    prompt_text = (SKILL_ROOT / phase.prompt).read_text(encoding="utf-8").strip()
    context = "\n".join(
        [
            f"- Idea: {summary['idea'] or '(none recorded)'}",
            f"- Language: {summary['language'] or 'infer from the idea'}",
            f"- Genre: {summary['genre'] or 'infer'}",
            f"- Audience: {summary['audience'] or 'infer'}",
            f"- Title: {summary['title'] or 'none yet'}",
        ]
    )
    existing = "".join(
        f"## Current `{relative}`\n\n{text}\n\n" for relative, text in _existing_artifacts(project)
    )
    notes = author_notes(project)
    if notes:
        existing += (
            "## Author notes\n\n"
            "The author read the previous result and asked for these changes. They override the defaults above.\n\n"
            f"{notes}\n\n"
        )
    required = [output for output in phase.outputs if output != "manuscript/chapters"]
    required_lines = "\n".join(f"- `{item}`" for item in required)
    outline_rule = ""
    if "artifacts/05-outline.md" in required:
        outline_rule = (
            "\nIn `artifacts/05-outline.md`, every chapter must be its own Markdown heading, exactly "
            "`## Chapter N: Title` (or `## Capítulo N: Título` when the book is in Portuguese), numbered from 1 "
            "with no gaps, one heading per chapter. The runner locates chapters by these headings; bold lines, "
            "table rows and list items do not count.\n"
        )
    output_contract = (
        "# OUTPUT\n\n"
        "Return every required file as its own block. Each block starts with a line exactly like "
        "`=== FILE: <path> ===` followed by the complete Markdown content of that file. Required files:\n"
        f"{required_lines}\n{outline_rule}\n"
        "After the files, add one block starting with the line `=== STATE ===` holding these lines, filled "
        "from your decisions: `title:`, `genre:` (one or two words: thriller, literary, memoir, fantasy, scifi, "
        "romance, nonfiction), `audience:`, `language:` (ISO code), `target_length:` (in words). "
        "Nothing before the first block and nothing after the last.\n"
    )
    return (
        RUNNER_CONTRACT
        + prompt_text
        + "\n\n# PROJECT\n\n"
        + context
        + "\n\n"
        + existing
        + output_contract
    )


def author_notes(project: Path) -> str:
    """Notes the person typed at a point of agreement in the guided session (ADR 0009)."""
    path = project / "work" / "author-notes.md"
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def split_files(text: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Split a model reply into ``{relative path: content}`` and the state block."""
    markers = [(m.start(), m.end(), _clean_name(m.group(1)), "file") for m in _FILE_MARK.finditer(text)]
    markers += [(m.start(), m.end(), "", "state") for m in _STATE_MARK.finditer(text)]
    markers.sort()

    files: Dict[str, str] = {}
    state: Dict[str, str] = {}
    for index, (_, end, name, kind) in enumerate(markers):
        body_end = markers[index + 1][0] if index + 1 < len(markers) else len(text)
        body = _unfence(text[end:body_end].strip())
        if kind == "file":
            files[name] = body
        else:
            state.update(_parse_state(body))
    return files, state


def _existing_artifacts(project: Path) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    assumptions = project / "ASSUMPTIONS.md"
    if assumptions.exists():
        text = assumptions.read_text(encoding="utf-8").strip()
        if text and TEMPLATE_MARK not in text:
            found.append(("ASSUMPTIONS.md", text))
    for filename in ARTIFACT_HEADINGS:
        path = project / "artifacts" / filename
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text and TEMPLATE_MARK not in text:
            found.append((f"artifacts/{filename}", text))
    return found


def _clean_name(raw: str) -> str:
    name = raw.strip().strip("`").strip()
    name = name.replace("\\", "/")
    while name.startswith("./"):
        name = name[2:]
    return name


def _unfence(body: str) -> str:
    match = _FENCE.match(body)
    return match.group(1).strip() if match else body


def _parse_state(body: str) -> Dict[str, str]:
    state: Dict[str, str] = {}
    for line in body.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lstrip("-").strip().lower()
        value = value.strip().strip('"').strip("'")
        if key:
            state[key] = value
    return state
